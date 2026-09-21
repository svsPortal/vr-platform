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
 # Detect current live stream and upcoming broadcasts for this channel.
 live_items=get("search",{"part":"snippet","channelId":cfg["channelId"],"type":"video","eventType":"live","maxResults":5}).get("items",[])
 upcoming_items=get("search",{"part":"snippet","channelId":cfg["channelId"],"type":"video","eventType":"upcoming","order":"date","maxResults":5}).get("items",[])
 def broadcasts(items):
  ids=[x.get("id",{}).get("videoId") for x in items if x.get("id",{}).get("videoId")]
  if not ids:return []
  details=get("videos",{"part":"snippet,liveStreamingDetails","id":",".join(ids)}).get("items",[])
  return [{"id":x["id"],"title":x["snippet"]["title"],"thumbnail":x["snippet"].get("thumbnails",{}).get("high",x["snippet"].get("thumbnails",{}).get("medium",{})).get("url",""),"scheduledStartTime":x.get("liveStreamingDetails",{}).get("scheduledStartTime"),"actualStartTime":x.get("liveStreamingDetails",{}).get("actualStartTime"),"concurrentViewers":x.get("liveStreamingDetails",{}).get("concurrentViewers")} for x in details]
 live_broadcasts=broadcasts(live_items)
 upcoming=broadcasts(upcoming_items)
 now=datetime.now(timezone.utc);limit=now+timedelta(days=30)
 def within30(x):
  s=x.get("scheduledStartTime")
  if not s:return False
  try:
   d=datetime.fromisoformat(s.replace("Z","+00:00"))
   return now<=d<=limit
  except:return False
 upcoming=[x for x in upcoming if within30(x)]
 out.append({"name":sn["title"],"channelId":cfg["channelId"],"youtube":cfg["youtube"],"subs":f'{int(st.get("subscriberCount",0)):,}人' if "subscriberCount" in st else "非公開","avatar":sn.get("thumbnails",{}).get("high",sn.get("thumbnails",{}).get("default",{})).get("url"),"videos":vids,"shorts":shorts,"live":bool(live_broadcasts),"liveBroadcast":live_broadcasts[0] if live_broadcasts else None,"upcoming":upcoming[:3]})
from datetime import datetime,timezone,timedelta
os.makedirs("data",exist_ok=True)
with open("data/youtube.json","w",encoding="utf-8") as f:json.dump({"updatedAt":datetime.now(timezone.utc).isoformat(),"creators":out},f,ensure_ascii=False,indent=2)

# Discovery candidates: conservative, review-first. Never auto-publish.
known={x["channelId"] for x in CHANNELS}
queries=["新人Vtuber 個人勢","個人Vtuber 初配信","#新人Vtuber"]
found={}
for q in queries:
 try:
  sr=get("search",{"part":"snippet","q":q,"type":"channel","order":"date","maxResults":10,"regionCode":"JP","relevanceLanguage":"ja"}).get("items",[])
  for x in sr:
   cid=x.get("id",{}).get("channelId")
   if cid and cid not in known:found[cid]=x.get("snippet",{})
 except Exception as e:print("discovery search failed",q,e)
candidates=[]
if found:
 try:
  details=get("channels",{"part":"snippet,statistics","id":",".join(found.keys())}).get("items",[])
  for x in details:
   sn=x.get("snippet",{});st=x.get("statistics",{});subs=int(st.get("subscriberCount",0)) if "subscriberCount" in st else None
   text=(sn.get("title","")+" "+sn.get("description","")).lower()
   signals=[k for k in ["vtuber","vチューバー","バーチャル","個人勢","新人v"] if k in text]
   if signals and (subs is None or subs<=50000):
    candidates.append({"channelId":x["id"],"name":sn.get("title"),"description":sn.get("description","")[:500],"subs":subs,"avatar":sn.get("thumbnails",{}).get("high",sn.get("thumbnails",{}).get("default",{})).get("url"),"youtube":"https://www.youtube.com/channel/"+x["id"],"signals":signals,"status":"review"})
 except Exception as e:print("discovery details failed",e)
candidates.sort(key=lambda x:(x["subs"] is None,x["subs"] if x["subs"] is not None else 10**12))
with open("data/discovery-candidates.json","w",encoding="utf-8") as f:json.dump({"updatedAt":datetime.now(timezone.utc).isoformat(),"mode":"review-only","candidates":candidates[:30]},f,ensure_ascii=False,indent=2)
