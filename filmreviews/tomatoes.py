import requests
import json
from bs4 import BeautifulSoup
import movie_search
import concurrent.futures
import time
import random
import whoosh
from whoosh import fields
from whoosh import index
from whoosh.fields import Schema
from tqdm import tqdm
import re
import os, os.path
from analyzer import StandardAnalyzer_num
class tomatoes:

    def __init__(self,url = "https://www.rottentomatoes.com/m/"):
        self.url = url


    def movie_desc(self, param):
        desc = ""
        name = param[0]
        date = param[1]
        soup = param[2]

        #soup = BeautifulSoup(req.content, 'html.parser') 
        for i in soup.find_all('div', class_="movie_synopsis clamp clamp-6 js-clamp"):
            tmp = str(i.get_text()).replace('\n','')
            tmp = re.sub(' +', ' ', tmp)
            desc += tmp.strip()
        return desc
    
    @staticmethod
    def format_output(stringa):
        stringa = stringa.split(':')
        stringa = stringa[1].split(',')
        return stringa[0]
    @staticmethod
    def format_genres(stringa):
        stringa = stringa.split(':')
        stringa = stringa[1].split(',')
        return stringa
    @staticmethod
    def format_date(stringa):
        stringa = stringa.split(':')
        return stringa[1]

    
    def movie_info(self,param):
        resp = []
        name = param[0]
        date = param[1]
        soup = param[2] #era req
        direc = ''
        release_date = ''
        runtime = ''
        genres = ''
        #soup = BeautifulSoup(req.content, 'html.parser') 
        for i in soup.find_all('li', class_="meta-row clearfix"):
            tmp = str(i.get_text()).replace('\n','')
            tmp = re.sub(' +', ' ', tmp)
            resp.append(tmp.strip())
            for i in resp:
                if 'Director' in i:
                    direc = self.format_output(i)
                if 'Runtime' in i:
                    runtime = self.format_output(i)
                if 'Release Date' in i:
                    release_date = self.format_date(i)
                if 'Genre' in i:
                    genres = str(''.join(self.format_genres(i)))
        return (direc,runtime,release_date,genres)
        

    def movie_casts(self,param):
        resp = []
        name = param[0]
        date = param[1]
        soup = param[2]
        #soup = BeautifulSoup(req.content, 'html.parser') 
        count = 0
        for i in soup.find_all('a', class_="unstyled articleLink"):
                if(count == 3):
                    tmp = str(i.get_text()).replace('\n','')
                    tmp = tmp.replace('\t', '')
                    tmp = tmp.replace('\r','')
                    tmp = tmp.replace('\n', '')
                    resp.append(tmp.strip())
                if 'View All' in i.get_text():
                    count += 1
        return str(','.join(set(resp[:-1])))
    
    def movie_reviews(self, param):
        reviews = []
        name = param[0]
        date = param[1]
        req = requests.get(self.url+name+"/reviews/")
        if req.status_code != 404:
            soup = BeautifulSoup(req.content, 'html.parser')
            for i in soup.find_all('div', class_="review_desc"):
                review = str(i.get_text()).replace('\n','')
                review = review.replace('\t','')
                review = review.replace('\r', '')
                review = review.replace('Full Review', '')
                review = review.replace('|', '')
                review = re.sub(' +', ' ', review)
                reviews.append(review.strip())
        else:
            req = requests.get(self.url+name+'_'+date+"/reviews/")
            if req.status_code != 404:
                soup = BeautifulSoup(req.content, 'html.parser')
                for i in soup.find_all('div', class_="review_desc"):
                    review = str(i.get_text()).replace('\n','')
                    review = review.replace('\t','')
                    review = review.replace('\r', '')
                    review = review.replace('Full Review', '')
                    review = review.replace('|', '')
                    review = re.sub(' +', ' ', review)
                    reviews.append(review.strip())
            else:          
                print("not_exists: " + name)
        return reviews

    #TODO Aggiungere filto per troppi trattini, attraverso le regex massimo un trattino 
        
    @staticmethod
    def format_name(name):
        film_name = name.lower()
        film_name = film_name.replace(' ','_')
        film_name = film_name.replace('\'','')
        film_name = film_name.replace('-', '_')
        film_name = film_name.replace(',','')
        film_name = film_name.replace(':','')
        return str(film_name)

    def test_iter(self,data):
        for i in range(int(self.num_film)):
            film_name = tomatoes.format_name(data[str(i)]["name"])
            self.movie_reviews(film_name)


#TODO Spostaare i metodi per la costruzione dell'indice in questa classe (quelli presenti nel main)
class indexTomatoes(tomatoes):
    def __init__(self,data,url = "https://www.rottentomatoes.com/m/"):
        if not os.path.exists("indexdir"):
            os.mkdir("indexdir")
            self.schema = Schema(
                id = fields.ID(unique=True,stored=True),
                title=fields.TEXT(stored=True,analyzer=StandardAnalyzer_num()),  
                content=fields.TEXT(stored=True), 
                release_date=fields.TEXT(stored=True),
                reviews = fields.STORED,
                genres = fields.TEXT(stored=True),
                directors = fields.TEXT(stored=True),
                casts = fields.TEXT(stored=True),
                runtime = fields.TEXT(stored=True),
            )
            self.ix = index.create_in("indexdir", self.schema)
        else:
            self.ix = index.open_dir("indexdir")

        self.url = url
        self._MOVIES = []
        self.films = []
        for i in range(len(data["movies"])):
            self.films.append({'id':data["movies"][i]["id"],'title':data["movies"][i]["title"],'date':data["movies"][i]["release_date"]})

    #def scrape_all_information(self):
    def get_all_information_t(self):    
        with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
            executor.map(self.get_all_information, self.films)

    def get_all_information(self,film):

        name = self.format_name(film["title"])
        id_film = film["id"]
        param = [name,film["date"]]

        start = time.time()
        richiesta = requests.get(self.url+name)
        end = time.time()

        if end-start >= 6:
            print(end-start)
            time.sleep(15)
        elif end-start >= 2:
            print(end-start)
            time.sleep(5)

        if richiesta.status_code != 404:
            soup = BeautifulSoup(richiesta.content, 'html.parser')
            param.append(soup)
            desc = self.movie_desc(param)
            if desc != "":
                info = self.movie_info(param)
                casts = self.movie_casts(param)
                rev = self.movie_reviews(param)
                film_schema = {
                'title':film["title"],
                'id':id_film,
                'overview':desc,
                'directors':info[0],
                'casts':casts,
                'reviews':rev,
                'runtime':info[1],
                'release':info[2],
                'genre':info[3],}
                self._MOVIES.append(film_schema)
                print(film_schema)

                #print(film_schema["casts"])

        else:
            richiesta = requests.get(self.url+name+'_'+param[1])
            if richiesta.status_code != 404:
                soup = BeautifulSoup(richiesta.content, 'html.parser')
                param.append(soup)
                desc = self.movie_desc(param)
                if desc != "":
                    info = self.movie_info(param)
                    casts = self.movie_casts(param)
                    rev = self.movie_reviews(param)
                    film_schema = {'title':film["title"],'id':id_film,'overview':desc,'directors':info[0],'casts':casts,'reviews':rev,'runtime':info[1],'release':info[2],'genre':info[3]}
                    self._MOVIES.append(film_schema)

                    print(film_schema)
    
    def indexing(self):
        self.writer = self.ix.writer()
        ids = set()
        for i in tqdm(range(len(self._MOVIES))):
            with open('./test.txt','a') as openfile:
                openfile.write(self._MOVIES[i]["title"]+ '\n')
            if(self._MOVIES[i]["id"] not in ids):
                self.writer.add_document(
                    id=str(self._MOVIES[i]["id"]),
                    title=self._MOVIES[i]["title"],
                    content=self._MOVIES[i]["overview"],
                    release_date = self._MOVIES[i]["release"],
                    reviews=self._MOVIES[i]["reviews"],
                    genres=self._MOVIES[i]["genre"],
                    directors = self._MOVIES[i]["directors"],
                    casts=self._MOVIES[i]["casts"],
                    runtime = self._MOVIES[i]["runtime"],
                )
                ids.add(self._MOVIES[i]["id"])
        self.writer.commit()




# test = tomatoes('./index/index.json')
# print(test.movie_info([test.format_name('Spider-man'),'2001']))