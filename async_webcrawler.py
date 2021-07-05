from bs4 import BeautifulSoup
import urllib.request as urllib
from urllib.request import urlopen, Request
from selenium import webdriver 
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from multiprocessing import Pool, cpu_count
import time
import os
import json
import gc
import sys

######## CUSTOM SEARCH PARAM ########
search_filter = "accepted_ans"  #anything else == show highest rating answer
intext_include = ""  #additional search criteria 
if len(sys.argv)==4:
	search_keyword = sys.argv[1]
	minimum_upvote = int(sys.argv[2])
	page_to_search = int(sys.argv[3]) 
else:
	search_keyword = sys.argv[1] or "How to learn as a programmer"
	minimum_upvote = 0
	page_to_search = 2  
#####################################
def trim(accepted_ans:list)->list:
    counter = 0
    accepted_ans = accepted_ans[0].get_text().strip().split('\n')
    for index, i in enumerate(accepted_ans):
        if not i: counter+=1
        else: 
            if counter >=3: del accepted_ans[index-counter:index]
            counter =0
    return accepted_ans 

def get_links(page_link:tuple)->list: 
    soup=""
    try:
        page_link, times = list(page_link)
        time.sleep(times/50)
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.3"}
        req = Request(url=page_link, headers = headers) 
        urls = urllib.urlopen(req)
        soup= BeautifulSoup(urls,'lxml')
        ans = ',\n'.join([str(link['href'])[7:] for link in (soup.select("div[class='kCrYT']>a"))])
        urls.close()
        with open('filename.txt', 'a+') as file_handle:
            file_handle.write(ans)
        pass     
    except Exception as err:
        print(err)
        print("Requests blocked by Google")
        return "no good!"
    if soup: soup.decompose()

def pool_wait(pool)->None:
        pool.close()
        pool.join()
        pool.terminate()

def store_data(link:list)->None:
    soup =""
    while True:
        if "stackoverflow.com/questions/" not in link: break
        print(link)
        try:
            start = time.perf_counter()
            response = urllib.urlopen(link)
            soup= BeautifulSoup(response,'lxml')
            response.close()
            print("Scraping website...")
            scores= [int(text.string) for text in soup.select("div[itemprop='upvoteCount']")]
            if (len(scores) < 2 or int(scores[1]) < minimum_upvote): break
            header= soup.find(id="question-header").select("h1>a")[0].string
            question= trim(soup.select("div[itemprop='text']"))
            
            if search_filter =="accepted_ans": 
                accepted_ans:list =trim(soup.select("div[itemprop='acceptedAnswer']")) or trim(soup.select("div[itemprop='suggestedAnswer']"))
            else: 
                accepted_ans:list = trim(soup.select(f"div[data-score='{max(scores)}']"))
            
            data ={
                "link": link,
                "qScore": scores[0],
                "header":header,
                "question": question,
                "topScore": scores[1],
                "ans": accepted_ans
            }
            with open('filename.txt', "a") as file_handle:
                file_handle.write(json.dumps(data, indent = 4)+",\n")
            print(f'Finished in {round(time.perf_counter()-start,2)} seconds') 
            break
        except Exception as error:
            print(error)
            break
    if soup: soup.decompose()


if __name__ == '__main__':
    start = time.perf_counter()
    """1. Use Selenium to search inside the custom selection"""
    options = webdriver.chrome.options.Options()
    options.add_argument("--headless")
    driver = webdriver.Chrome(executable_path ='../chromedriver', options=options)
    driver.get('http://www.google.com')
    q = driver.find_element(By.NAME, 'q')
    q.send_keys(f'{search_keyword} site:stackoverflow.com '+ Keys.ENTER)
    #intext:{intext_include}
    """2. Locate and save all the Google search result URLs inside a list"""
    WebDriverWait(driver, 2).until( 
        EC.presence_of_element_located((By.CLASS_NAME,'fl'))
        )
    pages=[driver.current_url]
    for page_num in range(2,page_to_search+1):
        url = driver.find_element_by_css_selector(f"[aria-label='Page {page_num}']").get_attribute('href')
        if url: pages.append(url)
        else: break
    pages = zip(pages, list(range(1,len(pages)+1))) #zip to better set timeinterval between each call to avoid overload
    

    """3. Now that we have a list of google search result URLs, we are going to 
          snatch all the StackOverflow urls inside each page (10 per page) """
    links,result = [], []
    # Attempts to spread the task to workers and call each page via urllib. 
    # If Google denies my search, the program switches over to the slower method below
    with Pool(cpu_count()*2) as pool:
        print("Gathering all the links...")
        result= pool.map(func = get_links, iterable = pages)
        pool_wait(pool)
    # Use Selenium to iterate through all the pages manually 
    if "no good!" in result:   
        for i in range(2,page_to_search+2): # page number starts at 2
            print("start of loop")
            WebDriverWait(driver, 10).until( 
            EC.presence_of_element_located((By.CLASS_NAME,'fl'))
            )
            links += [link.get_attribute('href') for link in (driver.find_elements_by_css_selector("[class='yuRUbf']>a"))]
            page = driver.find_element_by_css_selector(f"[aria-label='Page {i}']")
            page.click()        
    driver.quit()
    
    """4. I saved the URL result via urllib inside a file and the
          result via Selenium are saved inside a list. This step makes sure
          all the URLs are saved inside of a list to be used later on"""
    if not links:
        with open('filename.txt', 'r') as f:
            links =(f.read().split(","))
            os.remove("filename.txt")
    print(links)

    """5. Use multiproccessing & urllib to scrap through all the StackOverflow websites. The result
          is saved inside a .txt file to avoid picking error due to soup's infinite recursion"""
    with Pool(cpu_count()*2) as pool:
        try:
            pool.map(func = store_data, iterable =links)
            pool_wait(pool)
        except Exception as err:
            print(err)
    
    """6. Parse the data inside the .txt file and print out the results with my desired format"""
    answers=[]
    with open('filename.txt', 'r') as file_handle:
        f = '[' + file_handle.read()[:-2] +']'
        answers = json.loads(f)
        os.remove("filename.txt")
    sorted_answers = sorted(answers, key = lambda item: int(item['topScore']),reverse = True)

    for index, answer in enumerate(sorted_answers):
        print('='*30 +f"{answer['link']}" +'='*30 +'\n')  
        print(str(answer["qScore"]) +"\n_____\n"+ answer["header"] +"\n\nQuestion: ")
        for line in answer["question"]:
            #if "   " in line: continue
            print(line)
        print("\n\n")
        for line in answer["ans"]:
            if line == str(answer["topScore"]): 
                print(line+"\n_________\nAnswer:")
                continue
            if "   Follow" in line or "edited " in line : break
            print(line)
    print(f"total time to finish = {round(time.perf_counter() - start,2)}")
    gc.collect()


