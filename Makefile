build:
	docker build -t sunplot .

test: build
	docker run -it -p 2000:5000 sunplot

deploy: build
	heroku stack:set container
	git push heroku