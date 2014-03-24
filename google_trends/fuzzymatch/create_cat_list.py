import json

# simple code to process the category data which Google embeds in the 
# trends page. Assumes that temp contains this JSON
with open("temp", "r") as handle:
    data = json.load(handle)
    
    def process(jdata, id_so_far="", name_so_far="", num_tabs=0):
        new_id = "{0}{1}{2}".format(id_so_far, "-" if id_so_far else "", jdata["id"])
        #new_name = "{0}{1}{2}".format(name_so_far, "->" if name_so_far else "", 
        #                    jdata["name"].encode("ascii", "ignore"))
        new_name = jdata["name"].encode("ascii", "ignore")
        print("{0}{1}: {2}".format("\t"*num_tabs, new_id, new_name))
        if "children" in jdata:
            for child in jdata["children"]:
                process(child, new_id, new_name, num_tabs+1)

    process(data)
