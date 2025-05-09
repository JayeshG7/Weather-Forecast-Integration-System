import asyncio
import aiohttp
import os
from datetime import datetime, timedelta, time
from aiohttp.web import RouteTableDef, run_app, Application, Request, Response, FileResponse, json_response
import google.generativeai as genai

routes = RouteTableDef()
weather_cache = {}
gemini_nudge_cache = {} # New cache for Gemini nudges

# Configure Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    gemini_model = genai.GenerativeModel('gemini-1.5-flash-latest')
else:
    print("WARNING: GEMINI_API_KEY not found. AI nudges will be disabled.")
    gemini_model = None

def uniform_name(course):
    course = ''.join(course.split()).upper()
    subj_end = 0
    while subj_end < len(course) and not course[subj_end].isdigit():
        subj_end = subj_end + 1
     
    subj = course[:subj_end]
    course_num = course[subj_end:]

    if course_num.isalpha() or not len(course_num) == 3:
        raise ValueError("Invalid Course Format")
    #print(subj, int(course_num))
    return subj, int(course_num)

def get_next(class_days, start_time):
    curr_time = datetime.now().astimezone()
    for offset in range(8):
        potential_next_day = curr_time + timedelta(days=offset)
        if potential_next_day.weekday() not in class_days:
            continue
        else:
            nextclass_datetime = datetime.combine(potential_next_day.date(), start_time).replace(tzinfo=curr_time.tzinfo)
            if curr_time < nextclass_datetime:
                return nextclass_datetime

    return None

async def generate_ai_nudge(weather_data, course_info):
    if not gemini_model:
        return "Enjoy your day, Illini!"

    temp = weather_data.get('temperature', 'N/A')
    condition = weather_data.get('shortForecast', 'Not available')
    course_name = course_info.get('courseName', 'your class')
    next_meeting_time_str = course_info.get('nextMeetingTime', 'the upcoming session')

    # Determine generalized time of day for cache key
    time_of_day_for_cache = "anytime"
    try:
        meeting_dt = datetime.strptime(next_meeting_time_str, '%Y-%m-%d %H:%M:%S')
        hour = meeting_dt.hour
        if 5 <= hour < 12:
            time_of_day_for_cache = "morning"
        elif 12 <= hour < 17:
            time_of_day_for_cache = "afternoon"
        elif 17 <= hour < 21:
            time_of_day_for_cache = "evening"
        else:
            time_of_day_for_cache = "night"
    except ValueError:
        pass # Keep "anytime" if parsing fails

    cache_key = (temp, condition, course_name, time_of_day_for_cache)

    if cache_key in gemini_nudge_cache:
        print(f"Returning cached Gemini nudge for key: {cache_key}")
        return gemini_nudge_cache[cache_key]

    print(f"Generating new Gemini nudge for key: {cache_key}")
    try:
        # Ensure readable_time is generated correctly even if original next_meeting_time_str was just a placeholder
        try:
            # Re-parse here if needed, or rely on the meeting_dt from above if parsing was successful
            parsed_meeting_dt = datetime.strptime(next_meeting_time_str, '%Y-%m-%d %H:%M:%S')
            readable_time = parsed_meeting_dt.strftime('%I:%M %p on %A')
        except ValueError:
            readable_time = next_meeting_time_str # Fallback to the original string

        prompt = f"""You are the Illini Weather Assistant, a friendly, slightly witty, and helpful AI for University of Illinois students.
        Your goal is to provide a concise (1-2 sentences) and actionable nudge based on the weather for their upcoming class.
        Incorporate UIUC-specific language or campus references if it feels natural. Be encouraging!

        Context:
        - Course: {course_name}
        - Next Class Time: {readable_time}
        - Weather Condition: {condition}
        - Temperature: {temp}°F

        Generate a personalized nudge for the student:"""

        response = await asyncio.to_thread(gemini_model.generate_content, prompt)
        
        ai_generated_nudge = "Weather looks interesting for your class! Be prepared." # Default fallback
        if response.text:
            ai_generated_nudge = response.text.strip()
        
        gemini_nudge_cache[cache_key] = ai_generated_nudge
        return ai_generated_nudge
            
    except Exception as e:
        print(f"Error generating AI nudge: {e}")
        # Do not cache errors, return a generic fallback
        return "Have a great class, Illini! Check the weather details to prepare."

@routes.get('/')
async def index(request : Request) -> FileResponse: # done for you
    return FileResponse("index.html")


@routes.post('/weather')
async def POST_weather(request : Request) -> Response:
    try:
        data = await request.json()
        course_input = data.get("course")
        if not course_input:
            return json_response({"error" : "No course provided"}, status=400)
        
        subj, num = uniform_name(course_input) 
        course_key = f"{subj} {num}"

        if course_key in weather_cache:
            return json_response(weather_cache[course_key])
        #print("Answer from cache")
        
        server_url = os.getenv('COURSES_MICROSERVICE_URL')
        if not server_url:
            return json_response({"error": "Course microservice configuration error"}, status=400)
        
        async with aiohttp.ClientSession() as session:
            # Fetch course data
            async with session.get(f"{server_url}/{subj}/{num}/") as rep:
                if rep.status != 200:
                    return json_response({"error" : "Course not found"}, status=400)
                course_data = await rep.json()
            
            days_str = course_data.get('Days of Week', '')
            start_str = course_data.get('Start Time', '')
            #print(days_str)
            #print(start_str)
            if not days_str or not start_str or days_str == "ARRANGED" or start_str == "ARRANGED":
                return json_response({"error" :f"Invalid or unplannable schedule for {course_key}"}, status=400)
            
            day_dict = {'M': 0, 'T': 1, 'W': 2, 'R': 3, 'F': 4, 'S':5, 'U':6}
            class_days = [day_dict[d] for d in days_str.replace(" ", "") if d in day_dict] 
            if not class_days:
                return json_response({"error" :f"Invalid days in schedule for {course_key}"}, status=400)

            try:
                start_time_obj = datetime.strptime(start_str, '%I:%M %p').time().replace(second=0)
            except ValueError:
                return json_response({"error" :f"Invalid time format for {course_key}"}, status=400)

            next_class_datetime = get_next(class_days, start_time_obj)
            if not next_class_datetime:
                return json_response({"error" :f"No upcoming class found for {course_key} within the next week"}, status=404)
            
            forecast_time = next_class_datetime.replace(minute=0, second=0)
            
            # Fetch weather data
            async with session.get(f"https://api.weather.gov/points/40.11,-88.24") as rep:
                if rep.status != 200:
                    return json_response({"error" :"Weather service unavailable"}, status=400)
                points = await rep.json()
                forecast_url = points['properties']['forecastHourly']
                #print("Successfully recieved the weather data")
            
            async with session.get(forecast_url) as rep:
                if rep.status != 200:
                    return json_response({"error" :"Weather forecast unavailable"}, status=400)
                forecast = await rep.json()
                #print("Successfully recieved the forcast data")

        found_period = None
        for period in forecast['properties']['periods']:
            period_start_time = datetime.strptime(period['startTime'], '%Y-%m-%dT%H:%M:%S%z').replace(second=0)
            if period_start_time == forecast_time:
                found_period = period
                break
        
        """
        matching_period = [
            for period in forecast['properties']['periods']
            if forecast_time == (datetime.strptime(period['startTime'], '%Y-%m-%dT%H:%M:%S%z'))
        ]
        """

        weather_details = {
            "temperature": "N/A" if not found_period else found_period['temperature'],
            "shortForecast": "Not available" if not found_period else found_period['shortForecast']
        }

        course_info_for_nudge = {
            "courseName": course_key,
            "nextMeetingTime": next_class_datetime.strftime('%Y-%m-%d %H:%M:%S')
        }
        ai_nudge = await generate_ai_nudge(weather_details, course_info_for_nudge)

        response = {
            "course": course_key,
            "nextCourseMeeting": next_class_datetime.strftime('%Y-%m-%d %H:%M:%S'),
            "forecastTime": forecast_time.strftime('%Y-%m-%d %H:%M:%S'),
            "temperature": weather_details["temperature"],
            "shortForecast": weather_details["shortForecast"],
            "ai_nudge": ai_nudge
        }
        weather_cache[course_key] = response
        return json_response(response)
    
    except ValueError as e:
        return json_response({"error": str(e)}, status=400)
    except Exception as e:
        print(f"Unhandled exception in POST_weather: {e}")
        import traceback
        traceback.print_exc()
        return json_response({"error": "An unexpected error occurred on the server."}, status=500)

@routes.get('/weatherCache')
async def get_cached_weather(request : Request) -> Response:
    return json_response(data=weather_cache if weather_cache else {})
    



if __name__ == '__main__': # done for you: run the app with custom host and port
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', type=str, default="0.0.0.0")
    parser.add_argument('-p','--port', type=int, default=5005)
    args = parser.parse_args()
    
    app = Application()
    app.add_routes(routes)
    run_app(app, host=args.host, port=args.port)

