with open('static/index.html', 'w', encoding='utf-8') as f:
    f.write(open('frontend/index.html', 'r', encoding='utf-8').read())
print('done')
