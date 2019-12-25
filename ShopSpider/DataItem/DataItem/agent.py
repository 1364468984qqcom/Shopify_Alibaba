# -*- coding:utf-8 -*-
# 代理模块

import random

#: Agent代理
agents = [
    "Mozilla/5.0(Macintosh;U;IntelMacOSX10_6_8;en-us)AppleWebKit/534.50(KHTML,likeGecko)Version/5.1Safari/534.50",
    "Mozilla/5.0(Windows;U;WindowsNT6.1;en-us)AppleWebKit/534.50(KHTML,likeGecko)Version/5.1Safari/534.50",
    "Mozilla/5.0(compatible;MSIE9.0;WindowsNT6.1;Trident/5.0",
    "Mozilla/5.0(Macintosh;IntelMacOSX10.6;rv:2.0.1)Gecko/20100101Firefox/4.0.1",
    "Mozilla/5.0(WindowsNT6.1;rv:2.0.1)Gecko/20100101Firefox/4.0.1",
    "Mozilla/5.0(Macintosh;IntelMacOSX10_7_0)AppleWebKit/535.11(KHTML,likeGecko)Chrome/17.0.963.56Safari/535.11",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 Safari/537.36"
]

phone_agent = [
    "Mozilla/5.0 (Linux; U; Android 8.1.0; zh-cn; BLA-AL00 Build/HUAWEIBLA-AL00) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/57.0.2987.132 MQQBrowser/8.9 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 8.1; PAR-AL00 Build/HUAWEIPAR-AL00; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/57.0.2987.132 MQQBrowser/6.2 TBS/044304 Mobile Safari/537.36 MicroMessenger/6.7.3.1360(0x26070333) NetType/WIFI Language/zh_CN Process/tools",
    "Mozilla/5.0 (Linux; Android 8.1.0; ALP-AL00 Build/HUAWEIALP-AL00; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/63.0.3239.83 Mobile Safari/537.36 T7/10.13 baiduboxapp/10.13.0.11 (Baidu; P1 8.1.0)",
    "Mozilla/5.0 (Linux; Android 6.0.1; OPPO A57 Build/MMB29M; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/63.0.3239.83 Mobile Safari/537.36 T7/10.13 baiduboxapp/10.13.0.10 (Baidu; P1 6.0.1)",
    "Mozilla/5.0 (Linux; Android 8.1; EML-AL00 Build/HUAWEIEML-AL00; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/53.0.2785.143 Crosswalk/24.53.595.0 XWEB/358 MMWEBSDK/23 Mobile Safari/537.36 MicroMessenger/6.7.2.1340(0x2607023A) NetType/4G Language/zh_CN",
    "Mozilla/5.0 (Linux; Android 8.0; DUK-AL20 Build/HUAWEIDUK-AL20; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/57.0.2987.132 MQQBrowser/6.2 TBS/044353 Mobile Safari/537.36 MicroMessenger/6.7.3.1360(0x26070333) NetType/WIFI Language/zh_CN Process/tools",
    "Mozilla/5.0 (Linux; U; Android 8.0.0; zh-CN; MHA-AL00 Build/HUAWEIMHA-AL00) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/57.0.2987.108 UCBrowser/12.1.4.994 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 8.0; MHA-AL00 Build/HUAWEIMHA-AL00; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/57.0.2987.132 MQQBrowser/6.2 TBS/044304 Mobile Safari/537.36 MicroMessenger/6.7.3.1360(0x26070333) NetType/NON_NETWORK Language/zh_CN Process/tools",
    "Mozilla/5.0 (Linux; U; Android 8.0.0; zh-CN; MHA-AL00 Build/HUAWEIMHA-AL00) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/40.0.2214.89 UCBrowser/11.6.4.950 UWS/2.11.1.50 Mobile Safari/537.36 AliApp(DingTalk/4.5.8) com.alibaba.android.rimet/10380049 Channel/227200 language/zh-CN",
    "Mozilla/5.0 (Linux; U; Android 8.1.0; zh-CN; EML-AL00 Build/HUAWEIEML-AL00) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/57.0.2987.108 UCBrowser/11.9.4.974 UWS/2.13.1.48 Mobile Safari/537.36 AliApp(DingTalk/4.5.11) com.alibaba.android.rimet/10487439 Channel/227200 language/zh-CN",
    "Mozilla/5.0 (Linux; Android 8.0; MHA-AL00 Build/HUAWEIMHA-AL00; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/57.0.2987.132 MQQBrowser/6.2 TBS/044304 Mobile Safari/537.36 MicroMessenger/6.7.3.1360(0x26070333) NetType/4G Language/zh_CN Process/tools",
    "Mozilla/5.0 (Linux; U; Android 8.0.0; zh-CN; BAC-AL00 Build/HUAWEIBAC-AL00) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/57.0.2987.108 UCBrowser/11.9.4.974 UWS/2.13.1.48 Mobile Safari/537.36 AliApp(DingTalk/4.5.11) com.alibaba.android.rimet/10487439 Channel/227200 language/zh-CN",
    "Mozilla/5.0 (Linux; U; Android 8.1.0; zh-CN; BLA-AL00 Build/HUAWEIBLA-AL00) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/57.0.2987.108 UCBrowser/11.9.4.974 UWS/2.13.1.48 Mobile Safari/537.36 AliApp(DingTalk/4.5.11) com.alibaba.android.rimet/10487439 Channel/227200 language/zh-CN",
    "Mozilla/5.0 (Linux; Android 5.1.1; vivo X6S A Build/LMY47V; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/57.0.2987.132 MQQBrowser/6.2 TBS/044207 Mobile Safari/537.36 MicroMessenger/6.7.3.1340(0x26070332) NetType/4G Language/zh_CN Process/tools"
]

item_list_hd = {
    # 'accept-encoding': 'gzip, deflate, br',
    # 'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8,zh-TW;q=0.7',
    'user-agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 11_0 like Mac OS X) AppleWebKit/604.1.38 (KHTML, like Gecko) Version/11.0 Mobile/15A372 Safari/604.1',
    # 'accept': '*/*',
    # 'referer': 'https://h5.m.taobao.com/?sprefer=sypc00',
    # 'authority': 'h5api.m.taobao.com',
}

site_dict = {
    "http://products.kuyun.loc/api/screen/shop": {
        "url": "http://products.kuyun.loc/api/screen/product",
        "result": "http://products.kuyun.loc/api/screen/result",
        "headers": {
            "api-key": "admin@admin.org",
            "api-token": "TdPBrjxzpL+IFtIAv8q3Wp+IoROQNdD/wtmyABjbha4=",
            "Content-Type": "application/json"
        }
    },
    "http://testpl.kydev.org/api/screen/shop": {
        "url": "http://testpl.kydev.org/api/screen/product",
        "result": "http://testpl.kydev.org/api/screen/result",
        "headers": {
            "api-key": "kuyun@olmail.org",
            "api-token": "TdPBrjxzpL+IFtIAv8q3Wp+IoROQNdD/wtmyABjbha4=",
            "Content-Type": "application/json"
        }
    },
    "http://release.pl.kydev.org/api/screen/shop": {
        "url": "http://release.pl.kydev.org/api/screen/product",
        "result": "http://release.pl.kydev.org/api/screen/result",
        "headers": {
            "api-key": "kuyun@olmail.org",
            "api-token": "TdPBrjxzpL+IFtIAv8q3Wp+IoROQNdD/wtmyABjbha4=",
            "Content-Type": "application/json"
        }
    },
    "http://pl.kydev.org/api/screen/shop": {
        "url": "http://pl.kydev.org/api/screen/product",
        "result": "http://pl.kydev.org/api/screen/result",
        "headers": {
            "api-key": "kuyun@olmail.org",
            "api-token": "TdPBrjxzpL+IFtIAv8q3Wp+IoROQNdD/wtmyABjbha4=",
            "Content-Type": "application/json"
        }
    },
    "http://release.pl.kydev.org/api/screen/receive-video": {
        "headers": {
            "api-key": "kuyun@olmail.org",
            "api-token": "TdPBrjxzpL+IFtIAv8q3Wp+IoROQNdD/wtmyABjbha4=",
            "Content-Type": "application/json"
        }
    },
    "http://pl.kydev.org/api/screen/receive-video": {
        "headers": {
            "api-key": "kuyun@olmail.org",
            "api-token": "TdPBrjxzpL+IFtIAv8q3Wp+IoROQNdD/wtmyABjbha4=",
            "Content-Type": "application/json"
        }
    }
}


cookie1 = [
'lid=%E6%9C%89%E4%BA%9B%E6%B5%AE%E5%8A%A8%E7%9A%84%E5%BF%831314; cna=9YfJFDXP+j0CAT2WDO8LaBrJ; isg=BEVFskNNtbcqzZFr5KeanxLrV4G_qvva3lGPa0eqAXyL3mVQD1IJZNO86MKNhRFM; l=bBIZ6OHnv1d0cu8EKOCN5uI8UZbOSIOYYuPRwdXHi_5I16Lsya7OlrxZ4Fp6Vs5RsvYB4nhuVTp9-etki; otherx=e%3D1%26p%3D*%26s%3D0%26c%3D0%26f%3D0%26g%3D0%26t%3D0; x=__ll%3D-1%26_ato%3D0; t=e47fff023f1a844f6c364083516acd4d; _tb_token_=eb31e6e3ef9da; cookie2=1d4b288a07e5e84869f2c2a9bc60592b; OZ_SI_2061=sTime=1551077807&sIndex=35; OZ_1U_2061=vid=vc7391af90b2ca.0&ctime=1551079851&ltime=1551079836; OZ_1Y_2061=erefer=-&eurl=https%3A//uniqlo.tmall.com/shop/view_shop.htm%3Fspm%3Da230r.7195193.1997079397.2.6a9d3096tJ2IdE&etime=1551077807&ctime=1551079851&ltime=1551079836&compid=2061; hng=""; csg=3563ce84; skt=f1f8dae57df6cb9a; whl=-1%260%260%260; pnm_cku822=; swfstore=51377; uc1=cookie16=WqG3DMC9UpAPBHGz5QBErFxlCA%3D%3D&cookie21=URm48syIZx9a&cookie15=VT5L2FSpMGV7TQ%3D%3D&existShop=false&pas=0&cookie14=UoTZ5bOdhvQZNQ%3D%3D&tag=8&lng=zh_CN; uc3=vt3=F8dByEzYGUAphNYa6AU%3D&id2=UUphyu%2BFuPEh6vTG8w%3D%3D&nk2=sym%2Bm38XorfUm9qR&lg2=WqG3DMC9VAQiUQ%3D%3D; tracknick=%5Cu5C0F%5Cu6DD8%5Cu5728%5Cu8FD9%5Cu91CC%5Cu54E6; _l_g_=Ug%3D%3D; ck1=""; unb=2200611276482; lgc=%5Cu5C0F%5Cu6DD8%5Cu5728%5Cu8FD9%5Cu91CC%5Cu54E6; cookie1=WvcYrsYvf8SeBpzLgVOKCzkB7l%2BO8DCjR8ExuNJd2Qg%3D; login=true; cookie17=UUphyu%2BFuPEh6vTG8w%3D%3D; _nk_=%5Cu5C0F%5Cu6DD8%5Cu5728%5Cu8FD9%5Cu91CC%5Cu54E6; uss=""',
'isg=BPj4E_Yh0CjP5jyssaQfkH9YyqZKyV6lIyJi7DJpRDPmTZg32nEsew5vBYXYBhTD; l=bBIZ6OHnv1d0c1hQKOCN5uI8UZbOSIOYYuPRwdXHi_5Qp6Y_u5_Olrv2LFv6Vs5RsvYB4nhuVTp9-etki; dnk=%5Cu5C0F%5Cu6DD8%5Cu5728%5Cu8FD9%5Cu91CC%5Cu54E6; uc1=cookie14=UoTZ5bOSR6s7UQ%3D%3D&lng=zh_CN&cookie16=U%2BGCWk%2F74Mx5tgzv3dWpnhjPaQ%3D%3D&existShop=false&cookie21=VT5L2FSpdiBh&tag=8&cookie15=V32FPkk%2Fw0dUvg%3D%3D&pas=0; uc3=vt3=F8dByEzYGULsSbCX7WA%3D&id2=UUphyu%2BFuPEh6vTG8w%3D%3D&nk2=sym%2Bm38XorfUm9qR&lg2=UIHiLt3xD8xYTw%3D%3D; tracknick=%5Cu5C0F%5Cu6DD8%5Cu5728%5Cu8FD9%5Cu91CC%5Cu54E6; lid=%E5%B0%8F%E6%B7%98%E5%9C%A8%E8%BF%99%E9%87%8C%E5%93%A6; _l_g_=Ug%3D%3D; unb=2200611276482; lgc=%5Cu5C0F%5Cu6DD8%5Cu5728%5Cu8FD9%5Cu91CC%5Cu54E6; cookie1=WvcYrsYvf8SeBpzLgVOKCzkB7l%2BO8DCjR8ExuNJd2Qg%3D; login=true; cookie17=UUphyu%2BFuPEh6vTG8w%3D%3D; cookie2=137097e47ad566bd1afb42ded13670b7; _nk_=%5Cu5C0F%5Cu6DD8%5Cu5728%5Cu8FD9%5Cu91CC%5Cu54E6; t=1a08f0c16de76647474e1b99c9aba4af; sg=%E5%93%A625; csg=6555e41b; _tb_token_=353e5f35e4835; cna=yY76FFTaLnYCAT2WDJDeqia0; OZ_SI_2061=sTime=1551081799&sIndex=5; OZ_1U_2061=vid=vc73a148f869f8.0&ctime=1551081809&ltime=1551081806; OZ_1Y_2061=erefer=-&eurl=https%3A//uniqlo.tmall.com/shop/view_shop.htm%3Fspm%3Da230r.7195193.1997079397.2.6ec755e2BB8SBy&etime=1551081799&ctime=1551081809&ltime=1551081806&compid=2061; pnm_cku822=',
'isg=BJaWP03r1hL-5uK2Y5JZWq1W5ExYn9g_sZxcVgD_gnkUwzZdaMcqgfy1W5-K8NKJ; l=bBIZ6OHnv1d0c0lwKOCN5uI8UZbOSIOYYuPRwdXHi_5Zy6L_i6_OlrvfMFp6Vs5RsvYB4nhuVTp9-etki; dnk=%5Cu5C0F%5Cu6DD8%5Cu5728%5Cu8FD9%5Cu91CC%5Cu54E6; lid=%E5%B0%8F%E6%B7%98%E5%9C%A8%E8%BF%99%E9%87%8C%E5%93%A6; cookie2=137097e47ad566bd1afb42ded13670b7; t=1a08f0c16de76647474e1b99c9aba4af; csg=8679a32c; _tb_token_=353e5f35e4835; cna=yY76FFTaLnYCAT2WDJDeqia0; OZ_SI_2061=sTime=1551081799&sIndex=15; OZ_1U_2061=vid=vc73a148f869f8.0&ctime=1551081994&ltime=1551081989; OZ_1Y_2061=erefer=-&eurl=https%3A//uniqlo.tmall.com/shop/view_shop.htm%3Fspm%3Da230r.7195193.1997079397.2.6ec755e2BB8SBy&etime=1551081799&ctime=1551081994&ltime=1551081989&compid=2061; pnm_cku822=; otherx=e%3D1%26p%3D*%26s%3D0%26c%3D0%26f%3D0%26g%3D0%26t%3D0; swfstore=134473; whl=-1%260%260%260; x=__ll%3D-1%26_ato%3D0; hng=""; uc1=cookie16=W5iHLLyFPlMGbLDwA%2BdvAGZqLg%3D%3D&cookie21=V32FPkk%2FgihF%2FS5nr3O5&cookie15=Vq8l%2BKCLz3%2F65A%3D%3D&existShop=false&pas=0&cookie14=UoTZ5bOSR6U5qg%3D%3D&tag=8&lng=zh_CN; uc3=vt3=F8dByEzYGULiWepl3oY%3D&id2=W875Pb56bzoW&nk2=sFDBCfhCC4Rbcj0hvP6OIg%3D%3D&lg2=VFC%2FuZ9ayeYq2g%3D%3D; tracknick=%5Cu6709%5Cu4E9B%5Cu6D6E%5Cu52A8%5Cu7684%5Cu5FC31314; _l_g_=Ug%3D%3D; ck1=""; unb=874552232; lgc=%5Cu6709%5Cu4E9B%5Cu6D6E%5Cu52A8%5Cu7684%5Cu5FC31314; cookie1=VTlpO76IBWXpGp8V6b5O%2FBL4wWg5X0u327OeGfnIk0s%3D; login=true; cookie17=W875Pb56bzoW; _nk_=%5Cu6709%5Cu4E9B%5Cu6D6E%5Cu52A8%5Cu7684%5Cu5FC31314; uss=""; skt=1c622bec0639bf65',
]
