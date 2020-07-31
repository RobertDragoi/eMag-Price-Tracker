import requests
import smtplib, ssl
from bs4 import BeautifulSoup
import time
email=str(input("Enter your email: "))
password=str(input("Enter your password: "))
URL=str(input("Enter the product's URL:"))
def number(string):
    number=0
    for letter in string:
        if letter.isalnum()==True:
            number=number*10+int(letter,10)
    return number
def send_mail(message,email,password):
    context = ssl.create_default_context()
    server=smtplib.SMTP("smtp.gmail.com",587)
    server.ehlo() 
    server.starttls(context=context) 
    server.ehlo() 
    server.login(email,password)
    server.sendmail(email,email,message)

def check_price(URL):
    header={"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36"}
    page=requests.get(URL,headers=header)
    main=BeautifulSoup(page.content,'html.parser')
    price=main.find(class_="product-new-price").get_text()
    price=price.strip()
    price=number(price[0:len(price)-6])
    while True:
        previous_price=price
        price=main.find(class_="product-new-price").get_text()
        price=price.strip()
        price=number(price[0:len(price)-6])
        if price<previous_price:
            subject="Price was decreased by {}".format(previous_price-price)
            body="Check the link {}".format(URL)
            message=f"Subject: {subject} {body}"
            send_mail(message,email,password)
        else:
            print("Price is the same:",price)

        time.sleep(1800)
check_price(URL)