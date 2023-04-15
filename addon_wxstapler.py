from mitmproxy import ctx, http
import logging
import time
import os
import html
import json
import pdf_printer

# Global variables for the request template and article list
articles = []
template_flow = None

def response(flow: http.HTTPFlow) -> None:
    if "https://mp.weixin.qq.com/mp/profile_ext?action=getmsg" in flow.request.pretty_url:
        global articles
        
        # TODO: fix the bug for repeating tracking some of the traffic as the original traffic will be double requested!


        # Parse the response JSON and extract the 'has_next' field
        response_json = json.loads(flow.response.text)
        has_next = response_json['can_msg_continue']

        # Extract the articles from the response JSON and add them to the global list
        santinised_json_raw = response_json['general_msg_list'].replace("\/", "/")
        new_articles = json.loads(santinised_json_raw)['list']
        articles += flat_records_from(new_articles)

        # Modify the query parameters for the next request
        query_params = dict(flow.request.query.fields)

        offset = int(query_params.get('offset', '0')) if flow.is_replay else 0
        count = int(query_params.get('count', '10'))
        query_params['offset'] = str(offset + count) if flow.is_replay else offset

        replay_flow = flow.copy()
        replay_flow.request.query.fields = list(query_params.items())

        # Replay the request every 2 seconds while 'has_next' is true
        if has_next:
            time.sleep(2)
            ctx.master.commands.call("replay.client", [replay_flow])

        # Stop intercepting traffic once 'has_next' is false
        else:
            with open('articles.json', 'w', encoding='utf8') as f:
                json.dump(articles, f, ensure_ascii=False)

            logging.info('Finished capturing articles. Saved to articles.json')
            ctx.master.shutdown()

def done():
    logging.info('Done')

def replace_uncommon_characters(input_str):
    for s in ['(',')','|',' ','/','*','\\','.','<','>','&','?',' ']:
        output_str = input_str.replace(s, '-')
    return output_str

def sub_dict(data, keys):
    return {k: html.unescape(data[k]) for k in data if k in keys}

def sanitised_record(msg_info, p_date):
    date_pretty = time.strftime('%Y%m%d',time.localtime(p_date))

    keys = ['title', 'author', 'content_url', 'digest', 'cover', 'source_url']
    data = sub_dict(msg_info, keys)
    title = replace_uncommon_characters(data['title'])
    record_item = {}
    record_item['title'] = title
    record_item['date'] = date_pretty
    record_item['url'] = data['content_url']

    # record = "{}_{} : {}\n".format(date_pretty, title, data['content_url'])
    return record_item

def flat_records_from(msg_list):
    records = []
    for msg in msg_list:
        p_date = msg.get('comm_msg_info').get('datetime')

        msg_info = msg.get("app_msg_ext_info")

        if msg_info:
            multi_msg_info = msg_info.get("multi_app_msg_item_list")
            if multi_msg_info:
                for multi_msg_item in multi_msg_info:
                    records.append(sanitised_record(multi_msg_item, p_date))
            else:
                records.append(sanitised_record(msg_info, p_date))
        else:
            ctx.log.info(u"Non articles message，data=%s" % json.dumps(msg.get("comm_msg_info")))
    return records