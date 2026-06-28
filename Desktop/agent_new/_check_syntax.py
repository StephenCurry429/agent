import re

with open(r'c:\Users\Administrator\Desktop\agent\x-langchain\x-langchain\frontend\index.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Extract CSS
css_match = re.search(r'<style>(.*?)</style>', html, re.DOTALL)
if css_match:
    css = css_match.group(1)
    o = css.count('{')
    c = css.count('}')
    print(f'CSS: braces open={o} close={c} {"OK" if o==c else "MISMATCH!"}')

# Extract JS
js_match = re.search(r'<script>(.*?)</script>', html, re.DOTALL)
if js_match:
    js = js_match.group(1)
    a = js.count('{')
    b = js.count('}')
    c = js.count('(')
    d = js.count(')')
    e = js.count('[')
    f = js.count(']')
    print(f'JS:  {{{a}/{b}}}  ({c}/{d})  [{e}/{f}]')
    if a != b:
        print('WARNING: Curly brace mismatch!')
    if c != d:
        print('WARNING: Paren mismatch!')
    if e != f:
        print('WARNING: Bracket mismatch!')
