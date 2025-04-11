.PHONY: start test clean stop

start:
	python3 courses_microservice/schedules.py &
	COURSES_MICROSERVICE_URL=http://localhost:34001 python3 classweather.py

stop:
	pkill -f "python3 courses_microservice/schedules.py"
	pkill -f "python3 classweather.py"

clean: stop
	rm -f courses_microservice/*.jsonl
