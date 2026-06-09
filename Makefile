build:
	docker build -t wow-image .

rebuild:
	docker build --no-cache -t wow-image .

run:
	docker run -dit --name wow-container wow-image

shell:
	docker exec -it wow-container bash

clean:
	docker stop wow-container
	docker rm wow-container
