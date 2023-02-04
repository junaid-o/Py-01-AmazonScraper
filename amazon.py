from flask import Flask, render_template, request,jsonify
from flask_cors import CORS,cross_origin
import requests
from requests import Session
from bs4 import BeautifulSoup as bs
from urllib.request import urlopen as uReq

#################################
import pandas as pd
import re
import time
import cgi
import random
#######################################
#               DON'T TOUCH            #
########################################
class Amazon:

    ############################ Function For Searching the product ################################

    def search_product(search):
        count = 0  # count determine number of iteration in case except condition becomes true. Loop will broke ou as soon as first condition become true
        while count <= 50:
            try:
                amazon_url = "https://www.amazon.in/s?k=" + search
                uClient = uReq(amazon_url)
                amazonPage = uClient.read()
                uClient.close()
                # amazon_html = bs(amazonPage,'html.parser')
                # bigboxes = amazon_html.findAll("div", {"class":"s-card-container s-overflow-hidden aok-relative puis-include-content-margin puis s-latency-cf-section s-card-border"})
                print('Connection Established')
                break
            except Exception as e:
                print('Retrying: Check Your Internet Connection:', e)
                # continue
                time.sleep(2)
            count += 1

        return amazon_url
        # no_pages = 10

    ###################### Function for get product informaion displayed on search page ###########################

    def get_products_data(pageNo, amazon_url):
        headers = {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
            "accept-encoding": "gzip, deflate, br",
            "accept-language": "en-GB,en-US;q=0.9,en;q=0.8",
            "user-agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Mobile Safari/537.36",
        }

        # headers = {"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:66.0) Gecko/20100101 Firefox/66.0", "Accept-Encoding":"gzip, deflate", "Accept":"text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8", "DNT":"1","Connection":"close", "Upgrade-Insecure-Requests":"1"}
        # r = requests.get('https://www.amazon.in/gp/bestsellers/books/ref=zg_bs_pg_'+str(pageNo)+'?ie=UTF8&pg='+str(pageNo), headers=headers)#, proxies=proxies)

        count = 0
        while count <= 60:
            try:
                r = requests.get(amazon_url + '&page=' + str(pageNo), headers=headers)  # , proxies=proxies)
                search_result = r.content
                break
            except Exception as e:
                print("Retrying...", e)
                time.sleep(1)
            count += 1

        r.encoding = 'utf-8'
        # search_result = r.content
        soup = bs(search_result, 'html.parser')
        # print(soup)
        # results = soup.findAll('div', attrs={'data-component-type':'s-search-result'})
        # product_id.append(box.get("data-asin"))
        product_id = []
        alls = []

        for d in soup.findAll('div', attrs={'data-component-type': 's-search-result'}):
            # print(d)
            product_id.append(d.get("data-asin"))
            name = d.div.h2.span
            rating = d.find('span', {'class': 'a-icon-alt'})
            customer_rated = d.find('span', {"class": "a-size-mini a-color-base puis-light-weight-text"})
            discounted_price = d.find('span', {'class': 'a-offscreen'})
            price = d.find('div', {'class': "a-section a-spacing-none a-spacing-top-micro s-price-instructions-style"})
            discount = d.find("div", attrs={"class": "a-color-base"}).findAll("span",
                                                                              {"class": "puis-light-weight-text"})
            # print(discount)

            all1 = []
            if name is not None:
                all1.append(name.text)
                # print(name)
            else:
                all1.append("unknown-product")

            if rating is not None:
                # print(rating.text)
                all1.append(rating.text)
            else:
                all1.append('NA')

            if customer_rated is not None:
                # print(price.text)
                all1.append(customer_rated.text)
            else:
                all1.append('0')

            if discounted_price != []:
                # print(price.text)
                try:
                    all1.append(discounted_price.text)
                except:
                    return "Scrapping Error In Discounted Price"
            else:
                all1.append('NA')

            if discount != []:
                # print(price.text)
                try:
                    all1.append(discount[1].text)
                except:
                    all1.append(discount[0].text)
                    pass
            else:
                all1.append('NA')

            if price is not None:
                # print(price.text)
                try:
                    all1.append(price.find('span', {'class': 'a-text-price'}).span.text)
                    # print(price.div.find('span',{'class':'a-text-price'}).span.text)

                except Exception as e:

                    # return " Something Is Wrong In Scrapping Price"
                    all1.append(price.find('span', {'class': 'a-text-price'}))
                    pass
            else:
                all1.append('NA')
            alls.append(all1)

        return alls, product_id

    # get_data(1,amazon_url)

    ############## Function For Generating The Dataframe For Details Extracted from Search Page ####################

    def generate_detailed_df(number_of_pages_range, amazon_url):
        start_page = number_of_pages_range[0]
        end_page = number_of_pages_range[1]

        # no_pages= number_of_pages
        results = []
        results_all_other = []
        results_product_id = []

        for i in range(start_page, end_page + 1):
            count = 0
            while count <= 30:
                try:
                    print(f"Scrapping Page {i} of search results")

                    all_other, product_id = Amazon.get_products_data(i, amazon_url)
                    results_all_other.append(all_other)
                    results_product_id.append(product_id)
                    # print(f"Page {i} scrapped")
                    # print(len(results_all_other))
                    if (len(all_other) != 0 & len(product_id) != 0):
                        print(f"Page {i} scrapped")
                        #return f"Page {i} scrapped"
                    else:
                        print("Incomplete Scrapping: Few or Many Product May have been missed")
                        #print("We recommend you to retry after some time")

                    # print(product_id)
                    # flatten = lambda l: [item for sublist in l for item in sublist]
                    # df = pd.DataFrame(flatten(results_all_other),columns=['Product Name','Rating','Customers Rated','Dicounted Price', 'Discount','Price'])
                    # df.insert(0,"Product ID",flatten(results_product_id),allow_duplicates=True)
                    # Data Processing

                    break
                except:
                    print("Retrying...")
                    # continue
                    # time.sleep(3) # sleep time for execution of time
                count += 1

        flatten = lambda l: [item for sublist in l for item in sublist]
        df = pd.DataFrame(flatten(results_all_other),
                          columns=['ProductName', 'Rating', 'CustomersRated', 'DiscountedPrice', 'DiscountPercent', 'Price'])
        df.insert(0, "ProductID", flatten(results_product_id), allow_duplicates=True)

        df['Rating'] = df['Rating'].apply(lambda x: x.split()[0])

        df["Price"] = df["Price"].str.replace(',', '', regex=True)
        df["Price"] = df["Price"].str.replace('₹', '', regex=True)
        df["CustomersRated"] = df["CustomersRated"].str.replace('(', '', regex=True)
        df["CustomersRated"] = df["CustomersRated"].str.replace(')', '', regex=True)
        df["CustomersRated"] = df["CustomersRated"].str.replace(',', '', regex=True)
        df["DiscountPercent"] = df["DiscountPercent"].str.replace('(', '', regex=True)
        df["DiscountPercent"] = df["DiscountPercent"].str.replace(')', '', regex=True)
        df["DiscountPercent"] = df["DiscountPercent"].str.replace(' off', '', regex=True)
        df["DiscountPercent"] = df["DiscountPercent"].str.replace('%', '', regex=True)
        df["DiscountedPrice"] = df["DiscountedPrice"].str.replace('₹', '', regex=True)
        df["DiscountedPrice"] = df["DiscountedPrice"].str.replace(',', '', regex=True)
        #df.to_csv('amazon_products.csv', index=False, encoding='utf-8')  # Export Dataframe to csv

        return df

    ################### function for Getting list of All Major Links like all_review page,product_id, and product name list ########

    def get_products_review_link(amazon_url, pageNo_range):
        start_page = pageNo_range[0]
        end_page = pageNo_range[1]

        headers = {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
            "accept-encoding": "gzip, deflate, br",
            "accept-language": "en",
            "user-agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Mobile Safari/537.36",
        }

        # r = requests.get(amazon_url+'&page='+str(pageNo), headers=headers)#, proxies=proxies)
        # search_result = r.content
        amazon_search_page_list = []
        for page_no in range(start_page, end_page + 1):
            # print(page_no)
            amazon_search_page = amazon_url + f"&page={page_no}"
            # uClient = uReq(amazon_search_page)
            # amazonPage= uClient.read()
            # print(amazon_search_page)
            amazon_search_page_list.append(amazon_search_page)
            # uClient.close()
            # print(amazon_search_page_list)
        # r.encoding='utf-8'
        # search_result = r.content
        # soup = bs(search_result,'html.parser')

        # uClient = uReq(amazon_url)
        # amazonPage= uClient.read()
        # uClient.close()

        all_review_page_list = []
        product_id_list = []
        product_name_list = []

        for amazon_page_url in amazon_search_page_list:
            # print(amazon_page_url)
            r = requests.get(amazon_page_url, headers=headers)  # , proxies=u[0])
            search_result = r.content
            # uClient = uReq(amazon_page_url)
            # amazonPage= uClient.read()
            # uClient.close()
            amazon_html = bs(search_result, 'html.parser')
            # amazon_html;
            # Home Page for search results
            # bigboxes = amazon_html.findAll("div", {"class":"s-card-container s-overflow-hidden aok-relative puis-include-content-margin puis s-latency-cf-section s-card-border"})

            bigboxes = amazon_html.findAll('div', attrs={'data-component-type': 's-search-result'})
            # bigboxes;
            # print(len(bigboxes))

            # session = Session()
            # session.headers= headers
            # all_review_page_list = []
            # product_id_list = []
            # product_name_list=[]
            for box in bigboxes:
                # link_tag = box.find("a", attrs={'class':'a-link-normal s-no-outline'})
                try:
                    productLink = "https://www.amazon.in"+ box.div.div.div.div.a["href"]
                except:
                    productLink = "https://www.amazon.in"+ box.div.div.div.findAll('a')[0]['href']
                    #print(productLink)

                #productLink = "https://www.amazon.in" + box.div.div.div.div.a["href"]
                # print(productLink)
                index = productLink.find('dp/')
                see_all_review_page = productLink[:index] + "product-reviews" + productLink[index + 2:]
                # print(see_all_review_page)
                all_review_page_list.append(see_all_review_page)
                # links_tag_list.append("https://www.amazon.in"+ box.div.div.div.div.a["href"])
                product_id_list.append(box.get("data-asin"))
                product_name_list.append(box.div.h2.span)

        return product_id_list, product_name_list, all_review_page_list

    ################# Get Reviews Data Frame #######################################################

    def get_reviews(all_review_page_list, product_id, product_name, review_page_number_range):

        start_page = review_page_number_range[0]
        end_page = review_page_number_range[1]
        headers = {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
            "accept-encoding": "gzip, deflate, br",
            "accept-language": "en",
            "user-agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Mobile Safari/537.36",
        }

        # session = Session()
        # session.headers= headers
        customer_name_list = []
        rating_list = []
        review_title_list = []
        reviews_list = []
        product_ID_final = []
        product_name_final = []
        #index_for_product_id = iter([i for i in range(len(all_review_page_list))])
        id_idex = iter([i for i in range(len(product_id)+1)])
        name_idex = iter([i for i in range(len(product_name)+1)])
        for link in all_review_page_list:
            # print('productLink is: ',link)
            try:
                productID = product_id[next(id_idex)]
            except:
                productID = "NA"
            try:
                productName = product_name[next(name_idex)].text
            except:
                productName = "NA"

            #productID = product_id[next(index_for_product_id)]
            #productName = product_name[next(index_for_product_id)].text

            for review_page_number in range(start_page, end_page + 1):
                next_review_page_link = link + f"/ref=cm_cr_arp_d_paging_btm_2?ie=UTF8&pageNumber={review_page_number}&reviewerType=all_reviews"
                # print(next_review_page)
                next_review_page = requests.get(next_review_page_link, headers=headers, timeout=None)
                next_review_page.encoding = 'utf-8'
                next_review_page_soup = bs(next_review_page.content, "html.parser")
                profiles = next_review_page_soup.findAll("span", {"class": "a-profile-name"})
                # print(next_review_page_link)
                for i in range(len(profiles)):
                    customer_name = profiles[i].text
                    Review_title = next_review_page_soup.findAll('span', {
                        'class': "a-size-base review-title-content a-color-base a-text-bold",
                        'data-hook': "review-title"})[i].text
                    reviews = next_review_page_soup.findAll("span", {"data-hook": "review-body"})
                    rating = next_review_page_soup.findAll("span", {"class": "a-icon-alt"})[i].text
                    # print(next_review_page_link)
                    # print(product_name)
                    product_ID_final.append(productID)
                    product_name_final.append(productName)
                    customer_name_list.append(customer_name)
                    rating_list.append(rating)
                    #review_title_list.append(Review_title)
                    #reviews_list.append(reviews)
                    # time.sleep(random.randint(1,5))

                    if Review_title is not None:
                        try:
                            # print('try')
                            review_title_list.append(Review_title)
                        except:
                            # pass
                            review_title_list.append("NA")
                    else:
                        review_title_list.append("NA")

                    if reviews is not None:
                        try:
                            # print('try')
                            reviews_list.append(reviews[i].text)
                        except:
                            # pass
                            reviews_list.append("NA")
                    else:
                        reviews_list.append("NA")


        df = pd.DataFrame([product_ID_final,product_name_final, customer_name_list, rating_list, review_title_list, reviews_list]).T
        df.columns = ["Product ID","Product Name", 'Customer Name', 'Rating', 'Review Title', 'Reviews']
        df['Rating'] = df['Rating'].apply(lambda x: x.split()[0])
        df['Review Title'] = df['Review Title'].apply(lambda x: x.strip())
        df['Reviews'] = df['Reviews'].apply(lambda x: x.strip())
        #df.to_csv('amazon_products_reviews.csv', index=False, encoding='utf-8')  # Export Dataframe to csv
        return df


#######################################
app = Flask(__name__)

@app.route('/',methods=['GET'])  # route to display the home page
@cross_origin()
def homePage():
    return render_template("index.html")

@app.route('/analysis',methods=['POST','GET']) # route to show the review comments in a web UI

@cross_origin()
def index():
    if request.method == 'POST':
        try:
            searchString = request.form['content'].replace(" ","")
            startPage = request.form['startPage'].replace(" ","")
            endPage = request.form['endPage'].replace(" ","")
            review_startPage = request.form['reviewStartPage'].replace(" ","")
            review_endPage = request.form['reviewEndPage'].replace(" ","")

            radio = request.form['DataFrame']
            if radio=="DetailedDtaFrame":
                #print(radio)
                amazon_url = Amazon.search_product(searchString)
                summary_DataFrame = Amazon.generate_detailed_df([int(startPage),int(endPage)], amazon_url)
                Detailed_DataFrame = summary_DataFrame

                ######################################################
                #filename = searchString + ".html"
                #results1 = open(f"./templates/{filename}" ,"w",encoding="utf-8")
                #results1.write(Detailed_DataFrame.to_html())
                #results1.close
                ##############################################################

                #return render_template("results2.html", data=Detailed_DataFrame.to_html())
                #return analysis(Detailed_DataFrame)
                #return render_template(f"{filename}",analysis="Detailed_DataFrame", data=Detailed_DataFrame.to_html())
                ####################################################################################
            elif radio == "Reviews":
                amazon_url = Amazon.search_product(searchString)
                product_id, product_name, review_list = Amazon.get_products_review_link(amazon_url,[int(startPage),int(endPage)])
                #print(product_id)
                review_DataFrame = Amazon.get_reviews(review_list, product_id,product_name, review_page_number_range=[int(review_startPage),int(review_endPage)])
                Detailed_DataFrame = review_DataFrame
                #Detailed_DataFrame.to_csv('amazon_products_reviews.csv', index=False, encoding='utf-8')
                #Detailed_DataFrame.to_html("templates\DetailedDataFrame.html",classes='table table-stripped', render_links=True, show_dimensions=True)

                #############################################################################################################################
                #f = open("templates/results2.html", "w",,encoding='utf-8')
                #f.write("<a href='DetailedDataFrame.html' download='reviews.csv'>Download File</a>")
                #f.write(f"{bs(Detailed_DataFrame.to_html(classes='table table-stripped', render_links=True, show_dimensions=True)), 'html.parser'}",encoding="utf-8")

                ###################################################################################################################################

            f = open("templates/results2.html","w",encoding="utf-8")
            #f.write(Detailed_DataFrame.to_html(classes='table table-stripped', render_links=True, show_dimensions=True))
            #f.write("<a href='' download='reviews.csv'>Download File</a>\n\n" + Detailed_DataFrame.to_html(classes='table table-stripped', render_links=True, show_dimensions=True))
            script = open("templates/html_to_csv.html",'r+',encoding='utf-8')


            f.write(script.read() + Detailed_DataFrame.to_html(classes='table table-stripped', render_links=True, show_dimensions=True))
            f.close()

            #return Detailed_DataFrame.to_html(classes='table table-stripped',render_links=True,show_dimensions=True)
            #return render_template("DetailedDataFrame.html")   # Template should be template folder
            return render_template("results2.html",name=searchString)  # name has been used to push file name to be displayed on result page. here product name will be displayed


        except Exception as e:
            print('The Exception message is: ',e)
            return 'something is wrong'
            #return render_template(f"{filename}")
            # return render_template('results.html')

    else:
        return render_template('index.html')

if __name__ == "__main__":
    app.run(host='127.0.0.1', port=8001, debug=True)
	#app.run(debug=True)
