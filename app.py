from flask import Flask, render_template, request, current_app
from flask_cors import cross_origin
import requests
from bs4 import BeautifulSoup as bs
from urllib.request import urlopen as uReq
import pymongo
import pandas as pd
import logging
import time
import random
import os
import secrets
import string

#########################################################################################
#               FUNCTION TO CHECK FOR EMPTY LIST AND NESTED LIST                        #
#########################################################################################
def isListEmpty(inList):
    if isinstance(inList, list):  # Is a list
        return all(map(isListEmpty, inList))
    return False  # Not a list False means not empty list

########################################################################################
#               LOGIN TO MONGODB AND DATABASE AND COLLECTION CREATION                  #
#######################################################################################
#import pymongo

#  tls=True,tlsAllowInvalidCertificates=True
connection_string = os.getenv("MONGODB_CONNECTION_STRING")
#"mongodb+srv://amazon:OV3nZWFLCrKN6AHF@cluster0.sdazx6b.mongodb.net/?retryWrites=true&w=majority"
client = pymongo.MongoClient(connection_string,tls=True,tlsAllowInvalidCertificates=True)

# Database creation
db = client['amazon']

# Collection creation
collection_detailed = db['DetailedDataFrame']
collection_review = db['Reviews']
########### DELETE ENTIRE COLLECTION FROM SPECIFIC DATABASE ##############

#col.drop()
# Setting Index for text search
#db.review.create_index([('Product ID',pymongo.ASCENDING),
#                       ('ProductName', pymongo.ASCENDING),
#                       ('Reviews',pymongo.ASCENDING)])
######################################################################################
#                                                                                    #
#       GENERATING RANDOM STRING OF LENGTH 20 FOR DB DOWNLOAD LINK                   #
#                                                                                    #
######################################################################################

# import secrets
# import string
# initializing size of string
#download__review_link = ''.join(secrets.choice(string.ascii_uppercase + string.digits + string.ascii_lowercase + string.punctuation) for i in range(N))

N = 30
download__review_link = ''.join(secrets.choice(string.ascii_uppercase + string.digits + string.ascii_lowercase + ";,/?:@&=+$-_.!~*'()#")
                                for i in range(N))
download__detailed_link = ''.join(secrets.choice(string.ascii_uppercase + string.digits + string.ascii_lowercase + ";,/?:@&=+$-_.!~*'()#")
                                for i in range(N))


########################################################################################
#               DON'T TOUCH                                                            #
#               Class and Method Definition                                            #
########################################################################################

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
                logger_DEBUG.info('Amazon Connection Established')    ####### logging #######
                progressReport.info('Connection Established')  ####### logging #######
                break
            except Exception as e:
                print('Retrying: Check Your Internet Connection:', e)
                logger_DEBUG.warning('Retrying: Check Your Internet Connection:', e)  ####### logging #######
                progressReport.warning('Retrying.....',e)
                # continue
                time.sleep(random.uniform(random.random(),random.normalvariate(2,1)))
            count += 1
        logging.info("amazon url created")  ####### logging #######
        progressReport.info(f"searching for{search}")  ####### logging #######
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
                logging.info("Retrying...", e) #### Logging ####
                time.sleep(random.uniform(random.random(),random.normalvariate(3,1)))
            count += 1

        r.encoding = 'utf-8'
        # search_result = r.content
        soup = bs(search_result, 'html.parser')
        product_cat = soup.findAll('div', attrs={'id': 'departments'})[1].span.text
        # print(soup)
        logger_DEBUG.info(f"soup prepared for pageNo {pageNo}") #### logging ####
        # results = soup.findAll('div', attrs={'data-component-type':'s-search-result'})
        # product_id.append(box.get("data-asin"))
        category = []
        product_id = []
        alls = []

        for d in soup.findAll('div', attrs={'data-component-type': 's-search-result'}):
            # print(d)
            try:
                logger_DEBUG.info(f'Scraping {pageNo}')
                category.append(product_cat)
                product_id.append(d.get("data-asin"))
                name = d.div.h2.span
                rating = d.find('span', {'class': 'a-icon-alt'})
                customer_rated = d.find('span', {"class": "a-size-mini a-color-base puis-light-weight-text"})
                discounted_price = d.find('span', {'class': 'a-offscreen'})
                price = d.find('div', {'class': "a-section a-spacing-none a-spacing-top-micro s-price-instructions-style"})
                discount = d.find("div", attrs={"class": "a-color-base"}).findAll("span",{"class": "puis-light-weight-text"})
                # print(discount)
            except Exception as e:
                #print(f'Error In Scraping {pageNo}', e)
                logger_DEBUG.error(f'Error In Scraping {pageNo}',e)  #### logging ####
                progressReport.error(f'Error In Scraping {pageNo}', e)  #### logging ####


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
                    logger_DEBUG.error(f'Scrapping Error In Discounted Price from {pageNo}', e)  #### logging ####
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


        return alls, product_id,category

    # get_data(1,amazon_url)

    ############## Function For Generating The Dataframe For Details Extracted from Search Page ####################

    def generate_detailed_df(number_of_pages_range, amazon_url):
        start_page = number_of_pages_range[0]
        end_page = number_of_pages_range[1]

        # no_pages= number_of_pages
        results = []
        results_all_other = []
        results_product_id = []
        product_category = []

        for i in range(start_page, end_page + 1):
            count = 0
            while count <= 30:
                try:
                    logger_DEBUG.info(f"Initializing get_product_data() for Scrapping Page {i} of search results")  ###### Logging ####
                    print(f"Scrapping Page {i} of search results")
                    logger_DEBUG.info(f"Scrapping Page {i} of search results") ###### Logging ####
                    progressReport.info(f"Scrapping Page {i} of search results")  ###### Logging ####

                    all_other, product_id, category = Amazon.get_products_data(i, amazon_url)
                    results_all_other.append(all_other)
                    results_product_id.append(product_id)
                    product_category.append(category)
                    # print(f"Page {i} scrapped")
                    # print(len(results_all_other))

                    #########################################################################
                    #     Checking If The A Particular Entry Is Present In Database or not  #
                    #     if not then upload it to DB                                       #
                    #########################################################################

                    flatten = lambda l: [item for sublist in l for item in sublist]
                    flattend_all_other=flatten([all_other])
                    for j in range(len(flattend_all_other)):
                        #print(flatten([x])[i][0])
                        #print(y[i])
                        #print([y[i],flatten([x])[i][0]])
                        #match.append([y[i],flatten([x])[i][0]])


                        ###########################################################################
                        #     Checking If The A Particular Entry Is Present In Database or not    #
                        #     if not then upload it to DB: amazon, collection: DetailedDataFrame  #
                        ###########################################################################

                        if collection_detailed.find_one({'Product Name': flattend_all_other[j][0],'Product ID': product_id[j]}) is None:

                            print('Match Not Found')
                            logger_DEBUG.info(f"ProductID {product_id[j]} from Page {i} is NOT IN MongoDB")  ###### Logging ####
                            progressReport.info(f"ProductID {product_id[j]} from Page {i} is NOT IN Database")  ###### Logging ####
                            df_up = pd.DataFrame([flattend_all_other[j]],columns=['Product Name','Rating','Customers Rated','Discounted Price', 'Discount','Price'])
                            #print(product_category[0][j])
                            #print(product_id[j])

                            df_up.insert(0, "Category", category[j], allow_duplicates=True)
                            df_up.insert(1,"Product ID", product_id[j],allow_duplicates=True)

                            collection_detailed.insert_many(df_up.to_dict('records'))  ######## UPLOADING DATA TO MongoDB
                            logger_DEBUG.info(f"ProductID {product_id[j]} from Page {i} UPLOADED TO MongoDB")  ###### Logging ####
                            #progressReport.info(f"ProductID {product_id[j]} from Page {j} UPLOADED TO Database")  ###### Logging ####

                        else:
                            #print('Match Found')
                            logger_DEBUG.info(f"ProductID {product_id[j]} from Page {i} IS IN MongoDB")  ###### Logging ####
                            progressReport.info(f"ProductID {product_id[j]} from Page {i} IS IN Database")  ###### Logging ####

                            pass
                        ###############################################################



                    if (isListEmpty(all_other)==False) and (isListEmpty(product_id)==False):
                        print(f"Page {i} scrapped")
                        logger_DEBUG.info(f"Page {i} scrapped") ###### Logging ####
                        progressReport.info(f"Page {i} scrapped")  ###### Logging ####
                        #return f"Page {i} scrapped"
                    else:
                        print(f"Incomplete Scrapping for page {i}: Few or Many Product May have been missed")
                        #print("We recommend you to retry after some time")
                        logger_DEBUG.info(f"Incomplete Scrapping For Page {i} : Few or Multiple Product May have been missed")  ###### Logging ####
                        progressReport.warning(f"Incomplete Scrapping For Page {i} : Few or Multiple Product May have been missed")  ###### Logging ####

                    # print(product_id)
                    # flatten = lambda l: [item for sublist in l for item in sublist]
                    # df = pd.DataFrame(flatten(results_all_other),columns=['Product Name','Rating','Customers Rated','Dicounted Price', 'Discount','Price'])
                    # df.insert(0,"Product ID",flatten(results_product_id),allow_duplicates=True)
                    # Data Processing

                    break
                except:
                    print("Retrying...")
                    logger_DEBUG.info(f"Retrying for page {i}...")  ###### Logging ####
                    progressReport.info(f"Retrying for page {i}...")  ###### Logging ####
                    # continue
                    # time.sleep(3) # sleep time for execution of time
                count += 1
            time.sleep(random.uniform(random.random(),random.normalvariate(4.4567209,1)))
        progressReport.info("Processing Scrapped Data")  #### logging ####
        flatten = lambda l: [item for sublist in l for item in sublist]
        df = pd.DataFrame(flatten(results_all_other),
                          columns=['ProductName', 'Rating', 'CustomersRated', 'DiscountedPrice', 'DiscountPercent', 'Price'])
        df.insert(1, "ProductID", flatten(results_product_id), allow_duplicates=True)
        df.insert(0, "Category", flatten(product_category), allow_duplicates=True)

        df['Rating'] = df['Rating'].apply(lambda x: x.split()[0])

        df["Price"] = df["Price"].str.replace(',', '', regex=True)
        #df["Price"] = df["Price"].str.replace('₹', '', regex=True)
        df['CustomersRated'] = df["CustomersRated"].str.replace('(', '', regex=True)
        df["CustomersRated"] = df["CustomersRated"].str.replace(')', '', regex=True)
        df["CustomersRated"] = df["CustomersRated"].str.replace(',', '', regex=True)
        df["DiscountPercent"] = df["DiscountPercent"].str.replace('(', '', regex=True)
        df["DiscountPercent"] = df["DiscountPercent"].str.replace(')', '', regex=True)
        df["DiscountPercent"] = df["DiscountPercent"].str.replace(' off', '', regex=True)
        #df["DiscountPercent"] = df["DiscountPercent"].str.replace('%', '', regex=True)
        #df["DiscountedPrice"] = df["DiscountedPrice"].str.replace('₹', '', regex=True)
        df["DiscountedPrice"] = df["DiscountedPrice"].str.replace(',', '', regex=True)
        #df.to_csv('amazon_products.csv', index=False, encoding='utf-8')  # Export Dataframe to csv

        return df

    ################### function for Getting list of All Major Links like all_review page,product_id, and product name list ########

    def get_products_review_link(amazon_url, pageNo_range):
        start_page = pageNo_range[0]
        end_page = pageNo_range[1]
        page_log = iter([i for i in range(start_page,end_page +1)])
        page_prog = iter([i for i in range(start_page, end_page + 1)])
        headers = {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
            "accept-encoding": "gzip, deflate, br",
            "accept-language": "en-GB,en-US;q=0.9,en;q=0.8",
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
            logger_DEBUG.info(f"amazon search page {page_no} url created") ##### loging #####
            progressReport.info(f"Scrapping search page {page_no}")  ####### logging #######
        # r.encoding='utf-8'
        # search_result = r.content
        # soup = bs(search_result,'html.parser')

        # uClient = uReq(amazon_url)
        # amazonPage= uClient.read()
        # uClient.close()

        all_review_page_list = []
        product_id_list = []
        product_name_list = []
        category = []
        for amazon_page_url in amazon_search_page_list:
            # print(amazon_page_url)
            r = requests.get(amazon_page_url, headers=headers)  # , proxies=u[0])
            search_result = r.content
            # uClient = uReq(amazon_page_url)
            # amazonPage= uClient.read()
            # uClient.close()
            amazon_html = bs(search_result, 'html.parser')
            # bigboxes = amazon_html.findAll("div", {"class":"s-card-container s-overflow-hidden aok-relative puis-include-content-margin puis s-latency-cf-section s-card-border"})
            category.append(amazon_html.findAll('div', attrs={'id': 'departments'})[1].span.text)
            bigboxes = amazon_html.findAll('div', attrs={'data-component-type': 's-search-result'})
            # bigboxes;
            # print(len(bigboxes))

            # session = Session()
            # session.headers= headers
            # all_review_page_list = []
            # product_id_list = []
            # product_name_list=[]
            logger_DEBUG.info(f"Creating product link for page {next(page_log)}")  ##### logging ####
            progressReport.info(f"Creating product link for page {next(page_prog)}")  ##### logging ####

            for box in bigboxes:
                # link_tag = box.find("a", attrs={'class':'a-link-normal s-no-outline'})
                try:
                    productLink = "https://www.amazon.in"+ box.div.div.div.div.a["href"]
                except:
                    productLink = "https://www.amazon.in"+ box.div.div.div.findAll('a')[0]['href']
                    #print(productLink)

                #logger_DEBUG.info(f"product link created for page {next(page)}")  ##### logging ####
                #progressReport.info(f"product link created for page {next(page)}")  ##### logging ####

                #productLink = "https://www.amazon.in" + box.div.div.div.div.a["href"]
                # print(productLink)
                index = productLink.find('dp/')
                see_all_review_page = productLink[:index] + "product-reviews" + productLink[index + 2:]
                # print(see_all_review_page)
                logger_DEBUG.info("'see all review page' link created")  ##### logging ####
                all_review_page_list.append(see_all_review_page)
                # links_tag_list.append("https://www.amazon.in"+ box.div.div.div.div.a["href"])
                product_id_list.append(box.get("data-asin"))
                product_name_list.append(box.div.h2.span)
            time.sleep(random.uniform(random.random(),random.normalvariate(3.74629,0.808)))
        return product_id_list, product_name_list, all_review_page_list, category

    ################# Get Reviews Data Frame #######################################################

    def get_reviews(all_review_page_list, product_id, product_name, category,review_page_number_range):

        start_page = review_page_number_range[0]
        end_page = review_page_number_range[1]
        #review_page = iter([i for i in range(start_page,end_page +1)])
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
        category_list =[]
        #index_for_product_id = iter([i for i in range(len(all_review_page_list))])
        id_idex = iter([i for i in range(len(product_id)+1)])
        name_idex = iter([i for i in range(len(product_name)+1)])
        for link in all_review_page_list:
            # print('productLink is: ',link)
            category_idex = iter([i for i in range(len(category) + 1)])
            try:
                productID = product_id[next(id_idex)]
            except:
                productID = "NA"
            try:
                productName = product_name[next(name_idex)].text
            except:
                productName = "NA"
            try:
                categ =  category[next(category_idex)]
                print(categ)
            except:
                categ = 'NA'

            #productID = product_id[next(index_for_product_id)]
            #productName = product_name[next(index_for_product_id)].text

            for review_page_number in range(start_page, end_page + 1):
                next_review_page_link = link + f"/ref=cm_cr_arp_d_paging_btm_2?ie=UTF8&pageNumber={review_page_number}&reviewerType=all_reviews"
                # print(next_review_page)

                logger_DEBUG.info(f"review page {review_page_number} link created")      ##### logging ####
                progressReport.info(f"Scrapping review page {review_page_number} for productID {productID}")  ####### logging #######

                count = 0
                while count <= 60:
                    try:
                        next_review_page = requests.get(next_review_page_link, headers=headers, timeout=None)
                        break
                    except Exception as e:
                        print(f'Error in getting Review Page {review_page_number} for Product ID {productID}')
                        logger_DEBUG.warning(f'Error in getting Review Page {review_page_number} for Product ID {productID} \n',e)
                        progressReport.warning(f'Error in getting Review Page {review_page_number} for Product ID {productID}')
                        progressReport.warning('Retrying.....',e)
                        time.sleep(random.uniform(random.random(),random.normalvariate(2.21875431,0.7)))
                    count += 1

                next_review_page.encoding = 'utf-8'
                next_review_page_soup = bs(next_review_page.content, "html.parser")
                profiles = next_review_page_soup.findAll("span", {"class": "a-profile-name"})
                Review_title = next_review_page_soup.findAll('span', {
                    'class': "a-size-base review-title-content a-color-base a-text-bold",
                    'data-hook': "review-title"})
                reviews = next_review_page_soup.findAll("span", {"data-hook": "review-body"})
                # print(next_review_page_link)

                for i in range(len(profiles)):
                    customer_name = profiles[i].text
                    #Review_title = next_review_page_soup.findAll('span', {'class': "a-size-base review-title-content a-color-base a-text-bold", 'data-hook': "review-title"})
                    #reviews = next_review_page_soup.findAll("span", {"data-hook": "review-body"})
                    rating = next_review_page_soup.findAll("span", {"class": "a-icon-alt"})[i].text
                    # print(next_review_page_link)
                    # print(product_name)
                    product_ID_final.append(productID)
                    product_name_final.append(productName)
                    customer_name_list.append(customer_name)
                    rating_list.append(rating)
                    category_list.append(categ)
                    #review_title_list.append(Review_title)
                    #reviews_list.append(reviews)
                    # time.sleep(random.randint(1,5))

                    if Review_title is not None:
                        try:
                            # print('try')
                            review_title_list.append(Review_title[i].text)
                        except:
                            # pass
                            # #print([i.text for i in Review_title])
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

                    #########################################################################
                    #     Checking If The A Particular Entry Is Present In Database or not  #
                    #     if not then upload it to DB: amazon, collection: Reviews          #
                    #########################################################################

                    if collection_review.find_one({'Product ID': productID, 'ProductName': productName, 'Reviews': reviews_list[i]}) is None:
                        print('Match Not Found')
                        logger_DEBUG.info(
                            f"Reviews for ProductID {productID} from Page {review_page_number} is NOT IN MongoDB")  ###### Logging ####
                        #progressReport.info(f"Reviews for ProductID {productID[review_page_number]} from Page {review_page_number} is NOT IN MongoDB")  ###### Logging ####

                        try:
                            df_up = pd.DataFrame([f"{category[0]}",productID, productName, customer_name, rating, review_title_list[i], reviews_list[i]]).T
                            df_up.columns = ["Category","Product ID", "ProductName", 'Customer Name', 'Rating', 'Review Title','Reviews']
                            logger_DEBUG.info(f"Reviews for ProductID {productID} from Page {review_page_number} is UPLOADED IN MongoDB")  ###### Logging ####
                            #progressReport.info(f"Reviews for ProductID {productID[productID]} from Page {review_page_number} is UPLOADED IN DADTABASE")  ###### Logging ####
                            #print(category_list)
                            collection_review.insert_many(df_up.to_dict('records'))
                        except:
                            df_up = pd.DataFrame([f"{category[0]}",productID, productName,customer_name, rating, review_title_list, reviews_list[i]]).T
                            df_up.columns = ["Category","Product ID","ProductName",'Customer Name','Rating','Review Title','Reviews']
                            collection_review.insert_many(df_up.to_dict('records'))
                            logger_DEBUG.info(
                                f"Reviews for ProductID {productID[review_page_number]} from Page {review_page_number} is UPLOADED IN MongoDB")  ###### Logging ####
                            #print(reviews[i].text)
                            #print(category_list)
                    else:
                        print('Match Found')
                        pass

                time.sleep(random.uniform(random.random(),random.normalvariate(3.53211102,0.909878)))
        logger_DEBUG.info("Processing Scrapped Data For Review")  ##### logging ####
        progressReport.info("Processing Scrapped Data For Review")  ##### logging ####

        df = pd.DataFrame([category_list,product_ID_final,product_name_final, customer_name_list, rating_list, review_title_list, reviews_list]).T
        df.columns = ["Category","Product ID","Product Name", 'Customer Name', 'Rating', 'Review Title', 'Reviews']
        df['Rating'] = df['Rating'].apply(lambda x: x.split()[0])
        df['Review Title'] = df['Review Title'].apply(lambda x: x.strip())
        df['Reviews'] = df['Reviews'].apply(lambda x: x.strip())
        #df.to_csv('amazon_products_reviews.csv', index=False, encoding='utf-8')  # Export Dataframe to csv
        return df

#######################################################################################
#       Writing Function for generating Log files                                     #
#       and progressReport for the display on web                                     #
#######################################################################################

formatter_log = logging.Formatter('%(asctime)s :: %(levelname)s :: LineNo.: %(lineno)d :: %(message)s')
formatter_progressReport = logging.Formatter('%(message)s')

def setup_logger(name, log_file,file_mode, level, formatter):
    """To setup as many loggers as you want"""

    handler = logging.FileHandler(log_file,mode=file_mode)
    handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)

    return logger

# first file logger
logger_DEBUG = setup_logger('DEBUG', 'static/Reports/log.log',file_mode='w',level= logging.DEBUG,formatter=formatter_log)
logger_DEBUG.info('This is just info message')

# second file logger
progressReport = setup_logger('INFO', 'static/Reports/progressReport.log',file_mode='w',level= logging.INFO,formatter=formatter_progressReport)
progressReport.info('')


####################################################################################################################
#                                  Main App Section                                                                #
####################################################################################################################

app = Flask(__name__)

@app.route('/',methods=['GET'])  # route to display the home page
@cross_origin()
def homePage():

    logger_DEBUG.info('Initializing Home Page') ###### logging ########

    return render_template("index.html")


#######################################################################################################
#                        ROUTE FOR DISPLAY OF FINAL RESULTS AND COMPUTATION                           #
#######################################################################################################



@app.route('/analysis',methods=['POST','GET']) # route to show the review comments in a web UI
@cross_origin()
def index():

    if request.method == 'POST':
        try:
            ######### Getting Data From HTML Form ######################

            searchString = request.form['content'].replace(" ","")
            startPage = request.form['startPage'].replace(" ","")
            endPage = request.form['endPage'].replace(" ","")
            review_startPage = request.form['reviewStartPage'].replace(" ","")
            review_endPage = request.form['reviewEndPage'].replace(" ","")
            radio = request.form['DataFrame']

            logger_DEBUG.info("Form Submitted successfully")    ####### logging #######
            progressReport.info("Form Submitted successfully")  ####### logging #######

            ################# Checking For Type of Data Choosen By The User ###########

            if radio=="DetailedDtaFrame":
                #print(radio)
                logger_DEBUG.info("Initializing search_product()")  ####### logging #######
                progressReport.info("connecting with amazon")  ####### logging #######
                amazon_url = Amazon.search_product(searchString)
                logger_DEBUG.info("Initializing generate_detailed_df()")  ####### logging #######
                progressReport.info("Feeding data for scrapping")
                summary_DataFrame = Amazon.generate_detailed_df([int(startPage),int(endPage)], amazon_url)
                Detailed_DataFrame = summary_DataFrame
                logger_DEBUG.info("Detailed DataFrame Generated") ####### logging #######
                progressReport.info("Detailed DataFrame Generated")  ####### logging #######

                #return render_template("results2.html", data=Detailed_DataFrame.to_html())
                #return analysis(Detailed_DataFrame)
                #return render_template(f"{filename}",analysis="Detailed_DataFrame", data=Detailed_DataFrame.to_html())
                ####################################################################################
            elif radio == "Reviews":
                logger_DEBUG.info("Initializing search_product()")  ####### logging #######
                progressReport.info("connecting with amazon")  ####### logging #######

                amazon_url = Amazon.search_product(searchString)

                logger_DEBUG.info("Initializing get_product_review_link()") ####### logging #######
                progressReport.info("Getting primary information for review scrapping")  ####### logging #######

                product_id, product_name, review_list, category = Amazon.get_products_review_link(amazon_url,[int(startPage),int(endPage)])
                #print(product_id)
                logger_DEBUG.info("Initializing get_reviews()")  ####### logging #######

                review_DataFrame = Amazon.get_reviews(review_list, product_id,product_name, category,review_page_number_range=[int(review_startPage),int(review_endPage)])
                Detailed_DataFrame = review_DataFrame

                logger_DEBUG.info('Reviews Scrapped') ####### logging #######
                progressReport.info("Reviews Scrapped")  ####### logging #######

                #Detailed_DataFrame.to_csv('amazon_products_reviews.csv', index=False, encoding='utf-8')
                #Detailed_DataFrame.to_html("templates\DetailedDataFrame.html",classes='table table-stripped', render_links=True, show_dimensions=True)

                #############################################################################################################################
                #f = open("templates/results2.html", "w",,encoding='utf-8')
                #f.write("<a href='DetailedDataFrame.html' download='reviews.csv'>Download File</a>")
                #f.write(f"{bs(Detailed_DataFrame.to_html(classes='table table-stripped', render_links=True, show_dimensions=True)), 'html.parser'}",encoding="utf-8")

                ###################################################################################################################################

            ######## results2.html file writting ##############

            logger_DEBUG.info("writing results2.html")  ####### logging #######
            progressReport.info("\nPreparing Results For Display.....")  ####### logging #######

            f = open("templates/results2.html","w",encoding="utf-8")
            script = open("templates/html_to_csv.html",'r+',encoding='utf-8')

            #f.write(Detailed_DataFrame.to_html(classes='table table-stripped', render_links=True, show_dimensions=True))
            #f.write("<a href='' download='reviews.csv'>Download File</a>\n\n" + Detailed_DataFrame.to_html(classes='table table-stripped', render_links=True, show_dimensions=True))
            #script_pagination = open("templates/table_pagination_end.html", 'r+', encoding='utf-8')
            #f.write(script.read() + itables.to_html_datatable(Detailed_DataFrame, style="table-layout:auto;width:50%;float:center;margin:auto;;scrollX=True; classes=display"))
            #f.write(script.read() + Detailed_DataFrame.to_html(classes='table table-striped', render_links=True, show_dimensions=True) + script_pagination.read())

            f.write(script.read() + Detailed_DataFrame.to_html(classes='table table-striped', render_links=True, show_dimensions=True))
            f.close()

            logger_DEBUG.info("results2.html file written") ####### logging #######
            # Opening file in write mode will clear the the data already existing in he file
            #time.sleep(5)

            with open('static/Reports/progressReport.log', 'w+'):
                pass

            #return Detailed_DataFrame.to_html(classes='table table-stripped',render_links=True,show_dimensions=True)
            #return render_template("DetailedDataFrame.html")   # Template should be template folder
            searchQuery = request.form['content']
            return render_template("results2.html",name=searchQuery)  # name has been used to push file name to be displayed on result page. here product name will be displayed


        except Exception as e:
            #print('The Exception message is: ',e)
            logger_DEBUG.warning('Exception: ', e)  ####### logging #######
            progressReport.warning('Exception: ', e)  ####### logging #######
            return f'something is wrong \n{e}'
            #return render_template(f"{filename}")
            # return render_template('results.html')

    else:
        logger_DEBUG.warning("request.method is not POST") ####### logging #######

        return render_template('index.html')

#######################################################################################################
#                        ROUTE FOR PROGRESS REPORT                                                    #
#######################################################################################################

@app.route('/log',methods=['POST','GET']) # route to show the progress report on web UI
@cross_origin()
def stream():
    """returns logging information"""
    try:
        log_info= open("static/Reports/progressReport.log",'r+')
        data = log_info.read()
    except:
        data = '<h1 align="center">Job Progress Will Be shown here!</h1>'
    return render_template('log.html', output=data)
    #return data
    #return Response(data, mimetype="text/plain", content_type="text/event-stream")

#######################################################################################################
#                        ROUTE FOR DOWNLOAD OF DETAILED DATAFRAME FROM MONGODB                        #
#######################################################################################################

@app.route(f'/{download__detailed_link}', methods=['POST', 'GET'])
@cross_origin()
def download_detailed():
    logger_DEBUG.info('Fetching Detailed Data from Database....')  ###### Logging #####
    d = []
    for i in collection_detailed.find():
        d.append(i)
        # print(pd.DataFrame(i,index=[0]))
    df = pd.DataFrame(d).drop('_id', axis=1)
    try:
        df['Rating'] = df['Rating'].apply(lambda x: x.split()[0])
        df["Price"] = df["Price"].str.replace(',', '', regex=True)
        #df["Price"] = df["Price"].str.replace('₹', '', regex=True)
        df["Customers Rated"] = df["Customers Rated"].str.replace('(', '', regex=True)
        df["Customers Rated"] = df["Customers Rated"].str.replace(')', '', regex=True)
        df["Customers Rated"] = df["Customers Rated"].str.replace(',', '', regex=True)
        df["Discount"] = df["Discount"].str.replace('(', '', regex=True)
        df["Discount"] = df["Discount"].str.replace(')', '', regex=True)
        df["Discount"] = df["Discount"].str.replace(' off', '', regex=True)
        #df["Discount"] = df["Discount"].str.replace('%', '', regex=True)
        #df["Discounted Price"] = df["Discounted Price"].str.replace('₹', '', regex=True)
        df["Discounted Price"] = df["Discounted Price"].str.replace(',', '', regex=True)
    except:
        pass
    df.to_csv("Database/db_detailed.csv",encoding='utf-8')

    logger_DEBUG.info('Fetching DetailedData completed....')  ###### Logging #####
    logger_DEBUG.info('Cleaning generatd files....')  ###### Logging #####
    progressReport.info('Fetching DetailedData completed....')  ###### Logging #####


    def generate():
        with open("Database/db_detailed.csv", encoding="utf8") as f:
            yield from f
        os.remove("Database/db_detailed.csv")

    r = current_app.response_class(generate(), mimetype='text/csv')
    r.headers.set('Content-Disposition', 'attachment', filename='data.csv')
    return r

    # return send_file("database/db_detailed.csv",as_attachment=True, attachment_filename ='DetailedData.csv',mimetype='text/csv',cache_timeout=0)
    # return send_file('db_detailed.csv',as_attachment=True, attachment_filename ='DetailedData.csv',mimetype='text/csv',cache_timeout=1)


#######################################################################################################
#                        ROUTE FOR DOWNLOAD OF REVIEW DATAFRAME FROM MONGODB                        #
#######################################################################################################

@app.route(f'/{download__review_link}', methods=['GET','POST'])
@cross_origin()
def download_reviews():
    logger_DEBUG.info('Fetching Reviews Data from Database....')  ###### Logging #####
    d = []
    for i in collection_review.find():
        d.append(i)
        # print(pd.DataFrame(i,index=[0]))
    df = pd.DataFrame(d).drop('_id', axis=1)
    try:
        df['Rating'] = df['Rating'].apply(lambda x: x.split()[0])
        df['Review Title'] = df['Review Title'].apply(lambda x: x.strip())
        df['Reviews'] = df['Reviews'].apply(lambda x: x.strip())
    except:
        pass
    df.to_csv("Database/db_reviews.csv", encoding='utf-8')  ###### Logging #####
    logger_DEBUG.info('Fetching Reviews completed....')  ###### Logging #####
    logger_DEBUG.info('Cleaning generatd files....')  ###### Logging #####
    progressReport.info('Fetching Reviews completed....')  ###### Logging #####
    def generate():
        with open("Database/db_reviews.csv", encoding="utf8") as f:
            yield from f
        os.remove("Database/db_reviews.csv")

    r = current_app.response_class(generate(), mimetype='text/csv')
    r.headers.set('Content-Disposition', 'attachment', filename='reviews.csv')
    return r


###########################################################################


if __name__ == "__main__":
    #app.run(host='127.0.0.1', port=8001, debug=True)
    #app.run(debug=True)
    app.run(host='0.0.0.0', debug=True)  # for hosting

