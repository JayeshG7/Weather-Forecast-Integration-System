import asyncio
import aiohttp
import os
from datetime import datetime, timedelta, time

from aiohttp.web import RouteTableDef, run_app, Application, Request, Response, FileResponse, json_response
routes = RouteTableDef()

weather_cache = {}

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


@routes.get('/')
async def index(request : Request) -> FileResponse: # done for you
    return FileResponse("index.html")


@routes.post('/weather')
async def POST_weather(request : Request) -> Response:
    data = await request.json()
    course = data["course"]
    if not course:
        return json_response({"error" : "error finding course"}, status=400)
    
    subj, num = uniform_name(course) 
    course_key = f"{subj} {num}"

    if course_key in weather_cache:
        return json_response(weather_cache[course_key])
        #print("Answer from cache")
    
    server_url = os.getenv('COURSES_MICROSERVICE_URL')
    if not server_url:
        return json_response({"error": "Course microservice configuration error"}, status=400)
    
    async with aiohttp.ClientSession().get(f"{server_url}/{subj}/{num}/") as rep:
        if rep.status != 200:
            return json_response({"error" : "Course not found"}, status= 400)
        else:
            course_data = await rep.json()
    
    days_str = course_data.get('Days of Week', '')
    start_str = course_data.get('Start Time', '')
    #print(days_str)
    #print(start_str)
    if not days_str or not start_str:
        return json_response({"error" :"Invalif course data"}, status = 400)
    
    day_dict = {'M': 0, 'T': 1, 'W': 2, 'R': 3, 'F': 4}

    class_days = [day_dict[d] for d in days_str if d in day_dict] 
    if not class_days:
        return json_response({"error" :"Invalif day of week in course data"}, status = 400)

    try:
        start_time = datetime.strptime(start_str, '%I:%M %p').time().replace(second=0)
    except ValueError:
        return json_response({"error" :"Invalid format"}, status = 400)

    next_class_datetime = get_next(class_days, start_time)
    
    forecast_time = next_class_datetime.replace(minute=0, second=0)
    async with aiohttp.ClientSession() as session:    
        async with session.get(f"https://api.weather.gov/points/40.11,-88.24") as rep:
            if rep.status == 200:
                points = await rep.json()
                forecast_url = points['properties']['forecastHourly']
                #print("Successfully recieved the weather data")
            else:
                return json_response({"error" :"Unable to forecast"}, status = 400)
            

        async with session.get(forecast_url) as rep:
            if rep.status == 200:
                forecast = await rep.json()
                #print("Successfully recieved the forcast data")
            else:
                return json_response({"error" :"Unable to forecast"}, status = 400)
 

    found = None
    for period in forecast['properties']['periods']:
        if (datetime.strptime(period['startTime'], '%Y-%m-%dT%H:%M:%S%z')).replace(second=0) == forecast_time:
            found = period
            break
    
    """
    matching_period = [
        for period in forecast['properties']['periods']
        if forecast_time == (datetime.strptime(period['startTime'], '%Y-%m-%dT%H:%M:%S%z'))
    ]
    """


    response = {
        "course": course_key,
        "nextCourseMeeting": next_class_datetime.strftime('%Y-%m-%d %H:%M:%S'),
        "forecastTime": forecast_time.strftime('%Y-%m-%d %H:%M:%S'),
        "temperature":  "forecast unavailable" if not found else found['temperature'],
        "shortForecast":"forecast unavailable" if not found else found['shortForecast']
    }
    weather_cache[course_key] = response
    return json_response(response)

@routes.get('/weatherCache')
async def get_cached_weather(request : Request) -> Response:
    if weather_cache:
        return json_response(data= weather_cache)
    else :
        return json_response({})
    



if __name__ == '__main__': # done for you: run the app with custom host and port
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', type=str, default="0.0.0.0")
    parser.add_argument('-p','--port', type=int, default=5005)
    args = parser.parse_args()
    
    app = Application()
    app.add_routes(routes)
    run_app(app, host=args.host, port=args.port)

