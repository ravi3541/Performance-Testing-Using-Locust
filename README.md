# Performance-Testing-Using-Locust

# To generate html report
## locust -f sequential_test_script.py --headless --host https://your.host.url/api -u 10 -r 2 --run-time 2m  --html=report.html

# To generate csv report
## locust -f sequential_test_script.py --headless --host https://your.host.url/api -u 10 -r 2 --run-time 2m --csv=report