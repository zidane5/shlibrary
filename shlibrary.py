from flask import Flask, request, abort, jsonify
from enum import Enum, unique
from server import app
from util import *
import requests

def get_userkey():
    with open(r"conf\key") as f:
        return f.readline()

userkey = get_userkey()

@unique
class ShlibParam(Enum):
    gj_name = "abn"

class ShlibDataMgr:

    def __check_shlib_params(self, args):
        for each_arg in args:
            if each_arg not in [item.value for item in ShlibParam]:
                abort(400)

    def __make_brief_info(self, book_info):
        return {f"{breif_key}" : book_info}

    def __make_detail_info(self, book_info):
        # get "data" part from { "result": "0", "data": {} }
        return {f"{detail_key}" : book_info.get("data")}

    def get_gj_detail_info(self):
        self.__check_shlib_params(request.args)
        gj_name = request.args[ShlibParam.gj_name.value]
        all_books = self.__qurey_brief_info_for(gj_name)
        check_resp_status(all_books)

        books = all_books.get("data")
        if books is None:
            return {f"{no_data}" : ""}
        else:
            book_infos = []
            for each_book in books:
                book_uri = each_book.get("uri")
                if book_uri is None or len(book_uri) == 0:
                    book_infos.append(self.__make_brief_info(each_book))
                else:
                    book_infos.append(self.__make_detail_info(self.__query_detail_info_for(book_uri)))
            return book_infos

    @respjson
    def __qurey_brief_info_for(self, ab_name):
        return requests.get(f"http://data1.library.sh.cn/gj/webapi/instances?title={ab_name}&key={userkey}")

    @respjson
    def __query_detail_info_for(self, ab_uri):
        return requests.get(f"http://data1.library.sh.cn/gj/webapi/instanceInfo?uri={ab_uri}&key={userkey}")

if __name__ == "__main__":
    #app.run(host = "0.0.0.0", port = 5000, debug=True)
    # TODO
    pass