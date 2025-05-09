.PHONY: start test clean stop

start:
	@echo "Starting services..."
	@python3 classweather.py --port 5005 & \
	python3 courses_microservice/schedules.py --port 34001 & \
	wait

stop:
	pkill -f "python3 courses_microservice/schedules.py"
	pkill -f "python3 classweather.py"

clean: stop
	rm -f courses_microservice/*.jsonl
