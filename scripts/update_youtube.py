import json,os,urllib.parse,urllib.request
API=os.environ["YOUTUBE_API_KEY"]
BASE="https://www.googleapis.com/youtube/v3/"
CHANNELS=[
 {"name":"雪明みてん","channelId":"UCPMbyTlim27DvJtsa3kJHTQ","youtube":"https://www.youtube.com/@Yume_miten"},
 {"name":"天城リクト","channelId":"UCSMbl2XhcCjL-x_0yrrUU3g","youtube":"https://www.youtube.com/@Amagi_Rikuto"},
 {"name":"三毛猫わらび","channelId":"UC3bYL1a4b64ZYUy8Ow11H8g","youtube":"https://www.youtube.com/channel/UC3bYL1a4b64ZYUy8Ow11H8g"}
]
def get(path,params):
 params["key"]=API
 with urllib.request.urlopen(BASE+path+"?"+urllib.parse.urlencode(params),timeout=30) as r:return json.load(r)
out=[]
for cfg in CHANNELS:
 ch=get("channels",{"part":"snippet,statistics,contentDetails","id":cfg["channelId"]}).get("items",[])
 if not ch:continue
 ch=ch[0];sn=ch["snippet"];st=ch.get("statistics",{});uploads=ch["contentDetails"]["relatedPlaylists"]["uploads"]
 pl=get("playlistItems",{"part":"snippet,contentDetails","playlistId":uploads,"maxResults":8}).get("items",[])
 vids=[{"id":x["contentDetails"]["videoId"],"title":x["snippet"]["title"],"thumbnail":x["snippet"].get("thumbnails",{}).get("high",x["snippet"].get("thumbnails",{}).get("medium",{})).get("url",""),"publishedAt":x["snippet"].get("publishedAt")} for x in pl]
 # YouTube Data API has no definitive Shorts flag. Keep only explicit #shorts uploads
 shorts=[v for v in vids if "#shorts" in v["title"].lower()][:8]
 out.append({"name":sn["title"],"channelId":cfg["channelId"],"youtube":cfg["youtube"],"subs":f'{int(st.get("subscriberCount",0)):,}人' if "subscriberCount" in st else "非公開","avatar":sn.get("thumbnails",{}).get("high",sn.get("thumbnails",{}).get("default",{})).get("url"),"videos":vids,"shorts":shorts})
from datetime import datetime,timezone
os.makedirs("data",exist_ok=True)
with open("data/youtube.json","w",encoding="utf-8") as f:json.dump({"updatedAt":datetime.now(timezone.utc).isoformat(),"creators":out},f,ensure_ascii=False,indent=2)
