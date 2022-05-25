import requests
import json
from bs4 import BeautifulSoup
import index_gen


class tomatoes:
    url = "https://www.rottentomatoes.com/m/"
    path_index = index_gen.get_path()
    num_film = index_gen.create_index()

    def movie_info(self, name:str) -> str:
        desc = ""
        soup = BeautifulSoup(requests.get(self.url+str(name)).content, 'html.parser') 
        for i in soup.find_all('div', class_="movie_synopsis clamp clamp-6 js-clamp"):
            desc += i.get_text() 
        return desc
    
    def movie_reviews(self, name:str) -> str:
        reviews = []
        soup = BeautifulSoup(requests.get(self.url+str(name)+"/"+"reviews").content, 'html.parser') 
        for i in soup.find_all('div', class_="review_desc"):
            review = str(i.get_text()).replace('\n','')
            review = review.replace('\t','')
            review = review.replace('\r', '')
            review = review.replace('Full Review', '')
            review = review.replace('|', '')
            reviews.append(review)

        return reviews

test = tomatoes()
with open(test.path_index) as json_file:
    data = json.load(json_file)
    for i in range(test.num_film):
        for j in data[str(i)]["name"]:
            print(test.movie_info(j))
#for i in test.movie_reviews(input("Inserire nome film: ")):
    #print(i)
