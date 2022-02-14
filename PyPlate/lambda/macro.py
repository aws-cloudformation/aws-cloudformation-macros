import traceback


def obj_iterate(obj, params):
    if isinstance(obj, dict):
        for k in obj:
            obj[k] = obj_iterate(obj[k], params)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            obj[i] = obj_iterate(v, params)
    elif isinstance(obj, str):
        if obj.startswith("#!PyPlate"):
            params['output'] = None
            exec(obj, params)
            obj = params['output']
    return obj


def handler(event, context):
    macro_response = {
        "requestId": event["requestId"],
        "status": "success"
    }
    try:
        params = {
            "params": event["templateParameterValues"],
            "template": event["fragment"],
            "account_id": event["accountId"],
            "region": event["region"]
        }
        response = event["fragment"]
        macro_response["fragment"] = obj_iterate(response, params)
    except Exception as e:
        traceback.print_exc()
        macro_response["status"] = "failure"
        macro_response["errorMessage"] = str(e)

    return macro_response
