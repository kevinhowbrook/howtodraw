import requests
import json
import shutil
from PIL import Image, ImageDraw
import os
import math

from credentials import key

max_results = 40  # results per query
results_so_far = 0  # global reults counter to tell the loop to stop

keywords = ['How', 'To', 'Draw']  # What to search for


def get_total_items():
    url = 'https://www.googleapis.com/books/v1/volumes?q={}&maxResults={}&key={}'.format('+'.join(keywords), max_results, key)
    data = requests.get(url)
    data = json.loads(data.content)
    return(data['totalItems'])


def get_data(max_results, start_index):
    url = 'https://www.googleapis.com/books/v1/volumes?q={}&maxResults={}&startIndex={}&key={}'.format('+'.join(keywords), max_results, start_index, key)
    data = requests.get(url)
    data = json.loads(data.content)
    return data


# get total items and set to a local variable you can decrement when looping
total_items = get_total_items()
books = []

while results_so_far < 500:  # limit to 200 otherwise use total_items
    data = get_data(max_results, results_so_far)
    # get the items and title for the results and add to a list for writing to json
    if data and 'items' in data:
        items = data['items']
        for item in items:
            results_so_far += 1
            title = item['volumeInfo']['title']
            subtitle = ''
            image = ''
            if 'subtitle' in item['volumeInfo']:
                subtitle = ': ' + item['volumeInfo']['subtitle']
            if 'imageLinks' in item['volumeInfo']:
                url = item['volumeInfo']['imageLinks']['thumbnail']
                response = requests.get(url, stream=True)
                with open('images/img{}.jpeg'.format(results_so_far), 'wb') as out_file:
                    shutil.copyfileobj(response.raw, out_file)
                del response
                image = 'images/img{}.jpeg'.format(results_so_far)
            book = {
                'title': title,
                'subtitle': subtitle,
                'image': image
            }
            books.append(book)
    else:
        with open('data.json', 'w') as outfile:
            json.dump(books, outfile, ensure_ascii=False)
        continue


def get_max_image_size():
    file_paths = []
    directory = 'images'
    for filename in os.listdir(directory):
        if filename.endswith(".jpeg") or filename.endswith(".py"):
            file_paths.append(os.path.join(directory, filename))
        continue

    # Get the largest image size
    sizes = [Image.open(f, 'r').size for f in file_paths]
    max_size = max(sizes)
    return max_size


def resize_images():
    # Resize all the book image to be quare
    # Get all the image files
    file_paths = []
    directory = 'images'
    for filename in os.listdir(directory):
        if filename.endswith(".jpeg") or filename.endswith(".py"):
            file_paths.append(os.path.join(directory, filename))
        continue

    # Get the largest image size
    max_img_h = get_max_image_size()[1]

    for i in file_paths:
        # Each book image will be placed on a canvas of the max size.
        # so resave each image onto a new image with the new size
        img = Image.open(i, 'r')
        img_w, img_h = img.size
        filename = img.filename.replace('images/', '')
        # use largest height to make the canvas square
        background = Image.new('RGB', (max_img_h, max_img_h), (255, 255, 255))
        bg_w, bg_h = background.size
        offset = ((bg_w - img_w) // 2, (bg_h - img_h) // 2)
        background.paste(img, offset)
        background.save('images/resized/{}'.format(filename))


resize_images()


dir_name = 'images/resized'
numfiles = sum(1 for f in os.listdir(dir_name) if os.path.isfile(os.path.join(dir_name, f)) and f[0] != '.')


def calculate_m():
    # get a list of possible squared numbers, this give us the number of
    # rows and columns to use for the canvas, eg 4 = 2 x 2, 6 = 3 x 3...
    # Return: [] of squared numbers up to 10000 (hopefully we don't get that high!)
    m = []
    for i in range(1, 10000):
        m.append(i*i)
    return(m)


def grid(n, m):
    # given the amount of images, work out what grid or M we will need
    for i, m in enumerate(m):
        if m - n > 0 or m - n == 0:
            # loop stops when the amount of images can fit in a grid
            # eg ((m = 9) - (word_count = 5) = greater than 0 so use 9 (3x3)
            return float(m)
            break


# given we have a canvas size, now we can work out how many images will take up a row
m = math.sqrt(grid(numfiles, calculate_m()))


def make():
    canvas_size = int(m) * get_max_image_size()[1]
    im = Image.new('RGB', (canvas_size, canvas_size), color='white')  # draw the canvas
    # now we have a canvas. we will need to past and step through with the book images

    file_paths = []
    directory = 'images/resized'
    for filename in os.listdir(directory):
        if filename.endswith(".jpeg") or filename.endswith(".py"):
            file_paths.append(os.path.join(directory, filename))
        continue

    # if there are 3 squares to a row, we need to count 3 and increase
    # the starting drawing point in the order 0,333,666
    j = 0  # vertical counter
    k = 0  # horizontal counter
    s = get_max_image_size()[1]
    border_width = 0

    for i, v in enumerate(file_paths):
        squares_per_row = int(m)
        if i % squares_per_row == 0 and i != 0:
            j += 1
        if i % squares_per_row == 0 and i != 0:
            k = 0
        points = ((k*s, j*s), (k*s, j*s+s), (k*s+s, j*s+s), (k*s+s, j*s))
        book_img = Image.open(v, 'r')
        im.paste(book_img, points[0])
        ImageDraw.Draw(im).line((points[0], points[1], points[2], points[3], points[0]),  fill="white", width=border_width)
        k += 1

    im.save('allbooks.jpg')  # save the image.


make()
