import traceback


def handler(event, _):
    response = {
        "requestId": event["requestId"],
        "status": "success"
    }
    try:
        operation = event["params"]["Operation"]
        input = event["params"]["InputString"]

        no_param_string_funcs = ["Upper", "Lower", "Capitalize", "Title", "SwapCase"]

        if operation in no_param_string_funcs:
            response["fragment"] = getattr(input, operation.lower())()
        elif operation == "Strip":
            response["fragment"] = op_strip(event)
        elif operation == "Replace":
            response["fragment"] = op_replace(event)
        elif operation == "MaxLength":
            response["fragment"] = op_max_length(event)
        else:
            response["status"] = "failure"
    except Exception as e:
        traceback.print_exc()
        response["status"] = "failure"
        response["errorMessage"] = str(e)
    return response

def op_strip(event):
    chars = None
    input = event["params"]["InputString"]
    if "Chars" in event["params"]:
        chars = event["params"]["Chars"]
    return input.strip(chars)

def op_replace(event):
    return (
        event["params"]["InputString"]
        .replace(
            event['params']['Old'],
            event['params']['New'])
    )

def op_max_length(event):
    input = event["params"]["InputString"]
    length = int(event["params"]["Length"])
    strip_from = event["params"]["StripFrom"]

    if len(input) <= length:
        return input
    if strip_from == 'Right':
        return input[:length]
    return input[len(input)-length:]
