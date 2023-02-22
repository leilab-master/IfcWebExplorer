from flask import Flask, request,url_for, redirect,session
from flask import render_template,jsonify,Response
import flask, os, sys,time
import re
import copy
import time
import json
from gevent import pywsgi
import ifcopenshell
#from IfcFileReader import IfcFile
#from IfcSchemaReader import IfcSchema
interface_path = os.path.dirname(__file__)
sys.path.insert(0, interface_path)
app = Flask(__name__)

app.config['SECRET_KEY'] = os.urandom(24)
schema = None
ifcfile = None 
isInverse = None
invIDChoose = {}
@app.route('/')
def hello_world():
    return render_template("upload.html")

 
@app.route('/treeView',methods=['POST','GET'])
def treeView():
    ##If this jumps from /index, only the entityType is displayed
    if(request.referrer.find("index") > 0):
        global invIDChoose
        invIDChoose.clear()
        if(session.get("invIDChoose") != None):
            session.pop("invIDChoose")
        try:
            entityType = request.args['entityType']
        except:
            entityType = request.values.get("dl")
        session['entityType'] = entityType
        global isInverse
        try:
            isInverse = request.args['isInverse']
        except:
            isInverse = request.values.get("invText")
            pass
        return render_template("treeView.html")
    ##Otherwise it jumps back from /TreeView, and the child object is displayed
    else:
        #Click on the contents of the button row
        textName = request.get_json()['textName']
        #selectButtonID = request.args['selectButtonID']
        #session['selectButtonID'] = selectButtonID 
        #Get child objects
        #Click on the top button of EntityType
        if(re.search(r".*?\.ifc \[.*?\]:",textName) != None):
            #Get the object name
            entityName = re.search(r".*?\.ifc \[.*?\]: (.*?)\(",textName).group(1)
            entity_List = ifcfile.by_type(entityName)
            entityIDList = []
            for e in entity_List:
                entityIDList.append(str(e.id()))
            #entityIDList = copy.deepcopy(ifcfile.entsByName[entityName.upper()])#The set of IDs for all objects
            ##IDList is sorted by ID from smallest to largest
            #for i in range(0,len(entityIDList)):
                #entityIDList[i] = int(entityIDList[i])
            ##print(entityIDList)
            #entityIDList.sort()
            ##print(entityIDList)
            #for i in range(0,len(entityIDList)):
                #entityIDList[i] = str(entityIDList[i])
            return jsonify({"entityName": entityName, "entityIDList": entityIDList})

        #Determine the object name (# number)
        elif(re.search(r".*? \(#\d*?\)",textName) != None):
            #Get the object name
            entityID = re.search(r".*? \(#(\d*?)\)",textName).group(1)
            entity = ifcfile.by_id(int(entityID))
            entityAttributes = entity.get_info()
            #entityAttributes = copy.deepcopy(entity.get_info())
            del entityAttributes["id"],entityAttributes["type"]#删除多的id和type 
            #entityAttributes = copy.deepcopy(ifcfile.entById[int(entityID)]["attributes"])#Make sure you make a deepCopy.For a shallowCopy,the pointer changes the previous ifcfile
            #print(entityAttributes)
            for k,v in entityAttributes.items():
                if(v == None):
                    entityAttributes[k] = "$"
                elif(type(v) == ifcopenshell.entity_instance):#是否为entity_instance这个实例？
                    if(v.get_info()["id"] != 0):
                        v = "&lt" + v.get_info()["type"] + ":#" + str(v.id()) + "&gt"    
                        entityAttributes[k] = v
                    else:
                        entityAttributes[k] = v.get_info()["type"] + "(" + str(v.get_info()["wrappedValue"]) + ")"
                elif(type(v) == type("")):
                    entityAttributes[k] = v
                    #if(re.search(r"#\d*?",v) != None):
                        #pass
                        #attrEntityID = int(re.search(r"#(\d*)",v).group(1))
                        ##print(re.search(r"#(\d*)",v).group(1))
                        #attrEntityName = ifcfile.entById[attrEntityID]["name"]
                        
                        #for i in schema.entityNormalNames:
                            #if(i.upper() ==  attrEntityName):
                                #attrEntityName = i
                        #v = "&lt" + attrEntityName + ":#" + str(attrEntityID) + "&gt"                                                                                                                                                                               
                        #entityAttributes[k] = v
                    #If it's IFCTEXT, you need to omit it
                    
                    #elif(re.search(r"IFCTEXT\((.*?)\)",v) != None):
                        #entityAttributes[k] = re.search(r"IFCTEXT\((.*?)\)",v).group(1)
                        
                    #Normal string values require special parsing if they are in Japanese
                    #else:
                        #re_re=re.compile(r"(.*?)\\X2\\(.*?)\\X0\\")
                        #mo=re_re.search(v)
                        #subStr = ""
                        #temp = ""
                        #isJapanese = 0#Determine whether the annotation is Japanese
                        #while(mo):
                            #isJapanese = 1
                            #subStr = mo.group(0)
                            ##Get the non-Japanese part before subStr (because sometimes it's possible to combine Japanese with numbers and English)
                            #notJapanesePart = mo.group(1)
                            #str11=''
                            #v1=mo.group(2)
                            #list1=[v1[i:i+4] for i in range(0, len(v1), 4)]
                            #for i in range(len(list1)):
                                #str11=str11+(b'\\u'+bytes(list1[i],'unicode-escape')).decode('unicode-escape')
                            #temp = temp + notJapanesePart + str11
                            ##Remove the parsed part of all Japanese v (parsed part is \x2 + v + \x0, i.e. subStr)
                            #v = v.replace(subStr, "", 1)
                            #re_re=re.compile(r"(.*?)\\X2\\(.*?)\\X0\\")
                            #mo=re_re.search(v)
                            ##If mo is empty, then v may have some non-Japanese characters left, plus them
                            #if(not mo):
                                #temp = temp + v
                        #if(isJapanese == 1):
                            #entityAttributes[k] = temp
                elif(type(v) == tuple or type(v) == list):
                    temp = 0
                    for i in v:
                        if(type(i) == ifcopenshell.entity_instance):
                            temp = 1
                            break
                        #if(type(i) != ifcopenshell.entity_instance):#IFCPARAMETERVALUE这种也是entity_instance,要排除
                            #temp = 1
                            #break
                        #elif(i.get_info()["id"] == 0):
						    #entityAttributes[k] = i.get_info()["wrappedValue"]
							#temp = 1
                            #break
                        #if(type(i) != type("")):
                            #temp = 1
                            #break
                        #if(re.search(r"#\d*?",i) == None):
                            #temp = 1
                            #break
                    if(temp == 1):
                        entityAttributes[k] = "(" + str(len(v)) + ")"
                elif(type(v) == type(1.0)):
                    #Determines if it is a 10-bit timestamp
                    digit = 1#Default V is a floating-point number with an integer part of 1 bit
                    v1 = v
                    while(int(v1/10) != 0):
                        digit+=1
                        v1 = v1/10
                    if(digit == 10):  
                        #Convert to localtime
                        time_local = time.localtime(v)
                        #Convert to a new time format (2016-05-05 20:28:54)
                        dt = time.strftime("%Y-%m-%d %H:%M:%S",time_local)
                        entityAttributes[k] = dt
            #Determine whether the inverse is checked
            invList = []
            if(session.get("invIDChoose") == None or session.get("invIDChoose").get(entityID) == None):
                if(isInverse == "1"):
                    invIDChoose[entityID] = "1"
                    session["invIDChoose"] = invIDChoose
                    entityName = re.compile(r"\w+").findall(textName)[0]
                
                    EntityInvTypeList = entity.wrapped_data.get_inverse_attribute_names()#这个类型所有的INV，但是可能有的INV该实体没值，所以要下面区分
                    for invTypeName in EntityInvTypeList:
                        inverseEntities = entity.__getattr__(invTypeName)
                        if(len(inverseEntities)>0):
                            #m+=1
                            invStr = "INV:" + ' ' + invTypeName + "(" + str(len(inverseEntities)) + ")"
                            invList.append(invStr)
                            #print(invName)
                            #print(len(q))
                    
                    
                    
                    #inverseAttrsList = schema.getInverseAttrs(entityName.upper())
                    #for i in inverseAttrsList:
                        
                        #inverseEntities = []
                        #entities = ifcfile.getEntitiesBySuperName(i[1].upper())#Find all the underlying objects by the base class name
                        #if(len(entities) == 0):#See if the base class itself is the lowest level object
                            #try:
                                #entities = [ifcfile.entsByName[i[1].upper()]]
                            #except Exception:
                                #pass
                        #if(len(entities) != 0):
                            #for j in entities:#j is a set of entities of the same type
                                #for eID in j:
                                    #entity = ifcfile.entById[int(eID)]
                                    ##Iterate through the object
                                    #for k1,v1 in entity.items():
                                        #if(k1 == "attributes"):
                                            #for k2,v2 in v1.items():
                                                ##Stores the object if one of its attributes is the ID of the object you are now double-clicking on
                                                #if(type(v2).__name__ == "str"):
                                                    #if(v2 == "#"+entityID):
                                                        #inverseEntities.append(entity)
                                                #elif (type(v2).__name__ == "list"):
                                                    #for i1 in v2:
                                                        #if(i1 == "#"+entityID):
                                                            #inverseEntities.append(entity)
                            #if(len(inverseEntities) != 0):
                                #invStr = "INV:" + ' ' + i[0] + "(" + str(len(inverseEntities)) + ")"
                                #invList.append(invStr)
            #return jsonify({"entityAttributes": entityAttributes, "invList": invList})
            return Response(json.dumps({"entityAttributes": entityAttributes, "invList": invList}),mimetype='application/json')
        #Determine the attribute name = < attribute object name >
        elif(re.search(r".*? = <.*?:#\d*?>",textName) != None):
            entityName = re.search(r".*? = <(.*?):(#\d*?)>",textName).group(1)
            entityID = re.search(r".*? = <(.*?):(#\d*?)>",textName).group(2)
            
            #Case sensitivity
            #for i in schema.entityNormalNames:                                                                                                                                                 
                #if(i.upper() == entityName):
                    #entityName = i
            return jsonify({"entityName": entityName, "entityID": entityID})
        #Determine attribute name = (set length)
        elif(re.search(r".*? = \(\d*?\)",textName) != None):
            attrName = re.search(r"(.*?) = \(\d*?\)",textName).group(1)
            attrEntityNameAndID = request.get_json()['attrEntityNameAndID']
            attrEntityID = re.search(r".*? \(#(\d*?)\)",attrEntityNameAndID).group(1)
            #print(attrName + "?????" + attrEntityNameAndID + "???" + attrEntityID)
            
            entity = ifcfile.by_id(int(attrEntityID))
            attrList = entity.get_info()[attrName]
            #attrList = ifcfile.entById[int(attrEntityID)]["attributes"][attrName]
            attrDict = {}
            #print(attrList)
            for attrEntity in attrList:#i is#number
                #attrEntityID = int(re.search(r"#(\d*)",i).group(1))
                #attrEntityName = ifcfile.entById[int(attrEntityID)]["name"]
                #attrDict[str(attrEntityID)] = attrEntityName
                if(attrEntity.id()!=0):
                    attrDict[str(attrEntity.id())] = attrEntity.get_info()["type"]
                else:
                    attrDict[attrEntity.get_info()["type"]] = attrEntity.get_info()["wrappedValue"]
            #Case sensitivity
            #for k,v in attrDict.items():
                ##Unify the case of type names
                #for i in schema.entityNormalNames:
                    #if(i.upper() == v):
                        #attrDict[k] = i
            return jsonify({"attrDict": attrDict})
        #Determine INV: InvType
        elif(re.search(r"INV:",textName) != None):
            selectInverseName = re.search(r"INV: (.*)\(",textName).group(1)
            invEntityNameAndID = request.get_json()['invEntityNameAndID']
            entityName = re.search(r"(.*?) \(#(\d*?)\)",invEntityNameAndID).group(1)
            entityID = re.search(r"(.*?) \(#(\d*?)\)",invEntityNameAndID).group(2)
            
            entity = ifcfile.by_id(int(entityID))
            inverseEntitiesDict = {}
            EntityInvTypeList = entity.wrapped_data.get_inverse_attribute_names()#这个类型所有的INV，但是可能有的INV该实体没值，所以要下面区分
            for invTypeName in EntityInvTypeList:
                if(selectInverseName == invTypeName):
                    inverseEntities = entity.__getattr__(invTypeName)
                    for invEntity in inverseEntities:
                        inverseEntitiesDict[str(invEntity.id())] = invEntity.get_info()["type"]
                        session[str(invEntity.id())+selectInverseName] = invTypeName# ？？？？ This entity corresponds to the property name that is actually required in INV
                    #invStr = "INV:" + ' ' + invName + "(" + str(len(inverseEntities)) + ")"
            
            #inverseAttrsList = schema.getInverseAttrs(entityName.upper())
            #print(inverseAttrsList)
            #print(selectInverseName + "????" + invEntityNameAndID + "???" + entityName + "???" + entityID)
            
            #for i in inverseAttrsList:
                #if(selectInverseName == i[0]):#Get the same base class name as the inv type name, i[1]
                    #entities = ifcfile.getEntitiesBySuperName(i[1].upper())#Find all the underlying objects by the base class name
                    #if(len(entities) == 0):#See if the base class itself is the lowest level object
                        #try:
                            #entities = [ifcfile.entsByName[i[1].upper()]]
                        #except Exception:
                            #pass
                    #if(len(entities) != 0):
                        #for j in entities:#j is a set of entities of the same type
                            #for eID in j:
                                #entity = ifcfile.entById[int(eID)]
                                ##Iterate through the object
                                #for k1,v1 in entity.items():
                                    #if(k1 == "attributes"):
                                        #for k2,v2 in v1.items():
                                            ##Stores the object if its property value is the ID of the object you are clicking on
                                            #if(type(v2).__name__ == "str"):
                                                #if(v2 == "#"+entityID):
                                                    #inverseEntitiesDict[str(eID)] = entity["name"]
                                                    #session[str(eID)+selectInverseName] = i[2]#This entity corresponds to the property name that is actually required in INV
                                    
                                            #elif (type(v2).__name__ == "list"):
                                                #for i1 in v2:
                                                    #if(i1 == "#"+entityID):
                                                        #inverseEntitiesDict[str(eID)] = entity["name"]
                                                        #session[str(eID)+selectInverseName] = i[2]#This entity corresponds to the property name that is actually required in INV
                                                        
            ##Case sensitivity
            #for k,v in inverseEntitiesDict.items():
                ##Unify the case of type names
                #for i in schema.entityNormalNames:
                    #if(i.upper() == v):
                        #inverseEntitiesDict[k] = i
            #print(inverseEntitiesDict.items())
            return jsonify({"inverseEntitiesDict": inverseEntitiesDict})
        return textName
@app.route('/index/?<string:filename>')
def index(filename):
    #For the first time, read the IFC file in index, and then jump to the page directly
    if(session.get('filename') == None):
        session['filename'] = filename
        #Determine the schema type of the file
        schemaName = ""
        #global schema
        time1 = 0.0
        for line in open("static/" + filename):
            if(line.find('FILE_SCHEMA')!= -1):
                schemaName = re.search(r"FILE_SCHEMA *\(\('(.*?)'\)\);", line).group(1)
                #if(schemaName.find('4')!=-1):
                    ##Record when the file is imported
                    #t1 = time.time()    
                    #schema = IfcSchema("IFC4x2.exp")
                    #t2 = time.time()
                    #time1 = t2-t1
                    #print ("spend time on loading Schema:" + str(t2-t1))
                    #break
                #else:
                    #t1 = time.time()
                    #schema = IfcSchema("IFC2X3.exp")
                    #t2 = time.time()
                    #time1 = t2-t1
                    #print ("spend time on loading Schema:" + str(t2-t1))
                    #break
        fileCreateTime = ""
        for line in open("static/" + filename):
            if(line.find('FILE_NAME')!= -1):
                try:
                    fileCreateTime = re.search(r"FILE_NAME(.*?),(.*?),", line).group(2)
                except:
                    fileCreateTime = ""
                break
        fileCreateTime = fileCreateTime[1:-1]
        #session['schemaName'] = schemaName
        global ifcfile
        #Record when the file is imported
        t1 = time.time()
        ifcfile = ifcopenshell.open("static/" + filename)
        #ifcfile = IfcFile("static/" + filename, schema)
        t2 = time.time()
        time2 = round(float(t2-t1),2)
        print ("spend time on loading IFC:" + str(t2-t1))
        EntityTypeList = []
        totalEntities = len(ifcfile.wrapped_data.entity_names()) #Cumulate the number of entities in each category

        for ifcEntityType in ifcfile.wrapped_data.types():#ifcfile.entsByName
            typeCount = len(ifcfile.by_type(ifcEntityType))
            #typeCount = 0#The number of objects owned by the type
            #for i in range (0,len(ifcfile.entsByName[ifcEntityType])):
                #typeCount+=1
            ##Cumulate the number of entities in each category
            #totalEntities = totalEntities + typeCount

            ##Unify the case of type names 
            #for i in schema.entityNormalNames:
                #if(i.upper() == ifcEntityType):
                    #ifcEntityType = i
            EntityTypeList.append(str(ifcEntityType) + "(" + str(typeCount) + ")")
        EntityTypeList.sort()
        print("total number of entities:%d"%(totalEntities))
        #IFCAPPLICATION = ifcfile.entById[int(ifcfile.entsByName["IFCAPPLICATION"][0])]
        author = ""
        try:
            IFCAPPLICATION_id = ifcfile.by_type("IFCAPPLICATION")[0].id()
            IFCAPPLICATION = ifcfile.by_id(IFCAPPLICATION_id)
            author = IFCAPPLICATION.get_info()["ApplicationFullName"]
        except:
            pass
        #author = IFCAPPLICATION["attributes"]["ApplicationFullName"]
        
        session['ifc'] = {'filename': filename,'schemaName': schemaName,'EntityTypeList': EntityTypeList,"time1":time1,"time2":time2,"totalEntities":totalEntities,"author":author,"fileCreateTime":fileCreateTime}
        return render_template("index.html",ifc = session['ifc'])
    else:
        #ifc = {'filename': session['filename'],'schemaName': session['schemaName'],'EntityTypeList': session['EntityTypeList']}
        #return render_template("index.html",ifc = ifc)
        #print("22222")
        return render_template("index.html")

@app.route('/upload', methods=['GET','POST'])
def upload():
    #Clear all session
    session.clear()
    fname = request.files['filename']  #Get the uploaded file
    if fname:
        #t = time.strftime('%Y%m%d%H%M%S')Time markers
        new_fname = r'static/' + fname.filename
        fname.save(new_fname)  #Save the file to the specified path
        return redirect(url_for('index',filename=fname.filename))
    else:
        return '{"msg": "Please upload the file！"}' 

if __name__ == '__main__':
    #app.run(host='0.0.0.0',port=8080, debug=True)
    server = pywsgi.WSGIServer(('0.0.0.0', 8080),app)
    #server = make_server('127.0.0.1', 5000, app)
    server.serve_forever()
    app.run()
