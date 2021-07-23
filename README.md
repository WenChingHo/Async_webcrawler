# Super Stackoverflow Searcher (threading up to 100 urls at once)

## Table of contents
* [Intro / General info](#general-info)
* [Technologies](#technologies)
* Version 2 Changelog (#version-2-changelog)

## General info: 
A short project to practice and sum up my web crawling lectures. This program takes in command line arguments and perfrom a Google search on the topic with optional parameters. The crawler will then search through all the stackoverflow forums the comes up on google search and return either the highest-rated/accepted answer along with the question.


### Usage:
> python3 async_webcrawler topic [min_upvote] [pages_to_crawl]

search **5** page (10 links/page) = **50 links** and print the ones with a minimum upvote of **10**
> python3 async_webcrawler "Does HTML means how to meet ladies?" 10 5 


## Technologies:
- Python 3.9
- ~~selenium~~ 
- ~~urllib.request~~
- bs4 
- ~~multiprocessing ~~
- **VERSION 2 ADDITION:**
- requests
- threading
- OOP (attempt)


## Version 2 Changelog: 
- Removed selenium from code 
- Used requests instead or urllib.request
- Changed from multiporcessing to threading
- Packaged functions inside objects
- Removed all local variables
