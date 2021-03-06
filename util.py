from flask import request, abort, jsonify, render_template, redirect
from functools import wraps, lru_cache
from datetime import datetime, timedelta

DEBUG_ONLY = True

# region data

page_size = 10

## data server ip
def get_data_server():
    with open(r"conf\datasrv") as f:
        return f.readline()
data_server = get_data_server() # "http://47.97.124.135" # "http://localhost:2345"

resp_error_code = "error_code"
no_data = "no_data"
breif_key = "breif"
detail_key = "detail"
gjdetail_count_key = "count"
gjdetail_data_key = "data"

## index right
first_letter_key = "letter"
taxonomy_key = "taxonomy"
yn_region_key = "region"

## search resp json key
search_count_key = "count"
search_data_key = "data"
search_product_name_key = "product_name"
current_page_key = "current_page"
first_index_key = "first_index"
last_index_key = "last_index"
page_count_key = "page_count"
page_next_key = "page_next"
page_prev_key = "page_prev"
categories_key = "categories"
category_data_key = "category_data"
category_key = "category"

## detail resp json key
gj_list_key = "wcsource_qt"
gj_beautify_gj_list_key = "beautify_wcsource_qt"
gj_desc_key = "gjdesc"
wiki_info_key = "wiki_info"
related_poems_key = "poems"
map_location_key = "map_location"
wtime_key = "wtime"


## statistics
stat_fz_count_key = "count"
stat_fz_data_key = "data"
stat_map_location_key = "map_location"
stat_area_wccount_key = "stat_area_wccount"
stat_category_wccount_key = "stat_category_wccount"

## wiki type
baidu = "baidubaike"
hudong = "hudongbaike"
chinese = "zhwiki"

## poem key
poem_count_key = "count"
poem_data_key = "data"
poem_author = "author"
poem_title = "title"
poem_clause = "clause"

## action
search_simple = "RESTfulWS/JL/wc/fzwc"
search = "RESTfulWS/JL/wc/gjwc"
random_list = "RESTfulWS/JL/wc/list"
first_letter_list = "RESTfulWS/JL/wc/firstletter"
taxonomy_list = "RESTfulWS/JL/wc/taxonomy"
yn_region_list = "RESTfulWS/JL/wc/ynregion"

first_letter_info = "RESTfulWS/JL/wc/certainL"
taxonomy_info = "RESTfulWS/JL/wc/certainClass"
yn_region_info = "RESTfulWS/JL/wc/certainRegion"

wc_detail = "RESTfulWS/JL/jtwc/detail"
gj_detail = "RESTfulWS/JL/jtwc/gjdetail"
fz_detail = "RESTfulWS/JL/jtwc/lyfzDetail"
map_location = "RESTfulWS/JL/jtwc/lyplace"

wc_statistics_info = "RESTfulWS/JL/wc/tjwc"
fz_statistics_info = "RESTfulWS/JL/jtwc/allFZ"
wc_count_in_fz_info = "RESTfulWS/JL/jtwc/wcTJ"

# endregion data

# region decorator

def pick(count):
    def inner(func):
        import random
        @wraps(func)
        def wrapper(*args, **kwargs):
            lst = func(*args, **kwargs)
            if len(lst) <= count:
                return lst

            random.shuffle(lst)
            return lst[:count]

        return wrapper
    return inner

def jsut4test(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if DEBUG_ONLY:
            return func(*args, **kwargs)
        abort(404, "Page not found")

    return wrapper

def returnjson(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        return jsonify(func(*args, **kwargs))

    return wrapper

def returnHTML(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        return render_template(func(*args, **kwargs))

    return wrapper

def tryredirect(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        url = func(*args, **kwargs)
        if url == "":
            render_template("404.html")
        return redirect(url)

    return wrapper


def respjson(ignoreJSONDecodeError_UntilGetData = False, ignoreJSONDecodeError_Onetime = True):
    def inner(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            resp = func(*args, **kwargs)
            if resp.status_code == 200:
                if not ignoreJSONDecodeError_UntilGetData:
                    if ignoreJSONDecodeError_Onetime:
                        try:
                            return resp.json()
                        except ValueError: # from simplejson import JSONDecodeError
                            return {}
                    return resp.json()
                else:
                    def consume_exceptions(gen):
                        action = next(gen)
                        while True:
                            try:
                                json_result = action(*args, **kwargs).json()
                            except ValueError: # from simplejson import JSONDecodeError
                                json_result = None

                            try:
                                action = gen.send(json_result)
                            except StopIteration:
                                return json_result

                    def try_do_infinitely():
                        while True:
                            json_data = yield func
                            if json_data is not None:
                                # raise StopIteration() # error in Python3.7 
                                return
                            continue

                    return consume_exceptions(try_do_infinitely())

            return {f"{resp_error_code}" : resp.status_code }

        return wrapper
    return inner

# endregion decorator

# region help function

def get_request_params():
    if request.method == "POST":
        request_params = request.form
    elif request.method == "GET":
        request_params = request.args
    else:
        abort(500, "method not support")

    return request_params

def check_url_params(args, whichdict):
    for each_arg in args:
        if each_arg not in [item.value for item in whichdict]:
            abort(400, f"{each_arg} is not supported. Params supported: " + " ".join(enum.value for enum in whichdict))

def check_resp_status(content_json):
    if f"{resp_error_code}" in content_json:
        abort(500, "raw response status code: " + str(content_json.get(f"{resp_error_code}")))

# https://gist.github.com/Morreski/c1d08a3afa4040815eafd3891e16b945
def timed_cache(**timedelta_kwargs):
    def _wrapper(f):
        update_delta = timedelta(**timedelta_kwargs)
        next_update = datetime.utcnow() - update_delta
        # Apply @lru_cache to f with no cache size limit
        f = lru_cache(None)(f)

        @wraps(f)
        def _wrapped(*args, **kwargs):
            nonlocal next_update
            now = datetime.utcnow()
            if now >= next_update:
                f.cache_clear()
                next_update = now + update_delta

            try:
                return f(*args, **kwargs)
            except Exception as e:
                f.cache_clear()
                raise e

        return _wrapped
    return _wrapper

cache = timed_cache(hours = 2)

# endregion help function

# region etl for data

def remove_other_info_from_name(person_name):
    if not person_name:
        return ""

    temp_name = person_name.split(")")
    if len(temp_name) >= 2:
        temp_name = temp_name[1]
    else:
        temp_name = temp_name[0].split("）")
        if len(temp_name) >= 2:
            temp_name = temp_name[1]
        else:
            temp_name = temp_name[0]

    ends_dict = {
        "ends3" : ["续纂修"],
        "ends2" : ["增修", "纂修", "原纂", "续纂", "原修", "纂辑", "同纂", "增纂", "增订", "重校", "等纂"],
        "ends1" : ["纂", "修", "撰", "辑", "编", "校"]
    }
    for _, ends in ends_dict.items():
        for end in ends:
            if temp_name.endswith(end) and len(temp_name) > len(end) + 1:
                temp_name = temp_name.rstrip(end)
                return temp_name.strip()

    return temp_name.strip()

# endregion etl for data