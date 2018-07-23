from flask import Flask, render_template, request, redirect, url_for, flash, make_response, jsonify

app = Flask(__name__)


@app.route('/cookie/')
def cookie():
    if not request.cookies.get('dating'):
        res = make_response("Setting a cookie for 'dating'")
        res.set_cookie('dating', '1', max_age=60 * 60 * 24)
    else:
        cookie_value = int(request.cookies.get('dating'))
        res = make_response("Value of cookie 'dating' is {}, direct to www.tracker.com/dating?path={}".format(str(cookie_value), str(cookie_value)))
        cookie_value += 1
        if cookie_value % 5 == 0:
            cookie_value = 1
        res.set_cookie('dating', str(cookie_value), max_age=60 * 60 * 24)
    return res

if __name__ == '__main__':
    app.run()
