#!/Users/eddie/opt/anaconda3/bin/python3
from bs4 import BeautifulSoup
import requests
import threading
import time
import gc
import sys

HEADER = {
        "user-agent": 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36',
        'Connection':'close'
        }

class payload:
    url, data = [] , []
    COUNT, DROPPED, UNRELATED = (0,0,0)
    def __init__(self, keyword:str, search_type:str = 'top', upvote:int = 1, page:int = 5):
        self.keyword = keyword
        self.search_type = search_type
        self.upvote = int(upvote)
        self.page = int(page)

    def __repr__(self) -> str:
        return f'''------- Statistics -------------------
            Searched term: "{pl.keyword}""
            Minimun upvotes : {pl.upvote}
            Links crawled: {len(pl.url)}
            Links below minimum upload: {pl.DROPPED}
            Links unrelated: {pl.UNRELATED}
            *Links accept: {pl.COUNT}*
            Total time: {round(time.perf_counter() - start,2)} seconds \n'''

    def sort_data(self):
        self.data= sorted(self.data, key = lambda item: int(item['topScore']),reverse = True)
    
    def print_data(self):
        for answer in self.data:
            print('='*30 +f"{answer['link']}" +'='*30 +'\n')  
            print(answer["header"] +'\n\n'+ str(answer["qScore"]) + "\n_____\nQuestion: \n")
            for line in answer["question"]:
                if "Improve this question" in line: break
                print(line + "break")
            
            print("\n\n")
            for line in answer["ans"]:
                if line == str(answer["topScore"])+"\r": 
                    print(line+"\n_________\nAnswer:")
                    continue
                if "Improve this answer" in line or "edited " in line : break
                print(line)
                
class crawler(threading.Thread):
    def __init__(self, link, payload:payload):
        threading.Thread.__init__(self)
        self.link = link
        self.payload = payload
    def trim(self, accepted_ans:BeautifulSoup)->list:
        counter = 0
        index_difference = 0
        accepted_ans = accepted_ans[0].get_text().strip().split('\n')
        for index, i in enumerate(accepted_ans):
            if not i: counter+=1
            else: 
                if counter >=2: del accepted_ans[index-counter:index]
                index_difference +=counter
                counter =0
        return accepted_ans

    @staticmethod 
    def google_search(pl:payload):
        print("Proccessing search parameters and gathering all the links...")
        payload= {
        'start' : '0',
        'num' : pl.page*10,
        }
        url = (f"https://www.google.com/search?q={'+'.join(pl.keyword.split(' '))}+site%3A+www.stackoverflow.com")
        res = requests.get(url,params = payload, headers=HEADER)
        soup = BeautifulSoup(res.text,'lxml')
        # element type = bs4 tag. Include dict indexing method
        pl.url = [link['href'] for link in soup.select('div[class="yuRUbf"]>a')]
        soup.decompose()

    def run(self):
        soup =""
        while True:
            if "stackoverflow.com/questions/" not in self.link: 
                self.payload.UNRELATED +=1
                break
            try:
                response= requests.get(self.link, headers= HEADER)
                soup= BeautifulSoup(response.text,'lxml')
                print(f"Scraping {self.link}")
                scores= [int(text.string) for text in soup.select("div[itemprop='upvoteCount']")]
                # Check thread upvotes
                if (len(scores) < 2 or int(scores[1]) < self.payload.upvote): 
                    self.payload.DROPPED+=1
                    break
                header= soup.find(id="question-header").select("h1>a")[0].string
                question= self.trim(soup.select("div[itemprop='text']"))
                
                if self.payload.search_type =="accepted": 
                    accepted_ans:list =self.trim(soup.select("div[itemprop='acceptedAnswer']") or self.trim(soup.select("div[itemprop='suggestedAnswer']")))
                else: 
                    accepted_ans:list = self.trim(soup.select(f"div[data-score='{max(scores)}']"))
                data ={
                    "link": self.link,
                    "qScore": scores[0],
                    "header":header,
                    "question": question,
                    "topScore": scores[1],
                    "ans": accepted_ans
                    }    

                self.payload.data.append(data)
                self.payload.COUNT +=1
            except Exception as error:
                print(error)
                break
            if soup: soup.decompose()
            break
#####################################

if __name__ == '__main__':
    start = time.perf_counter()
    pl = payload(*sys.argv[1:])
    crawler.google_search(pl)

    for link in pl.url:
        crawler(link, pl).start()
    while threading.active_count() >1:
        time.sleep(0.1)
        print(threading.active_count())
    pl.sort_data()
    pl.print_data()
    gc.collect()
    print(pl)


