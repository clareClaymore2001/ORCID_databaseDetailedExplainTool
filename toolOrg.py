import os,time,random
import xml.etree.ElementTree as ET
import pandas as pd
import glob
import csv

import multiprocessing as mp
import concurrent.futures
from tqdm import tqdm
from joblib import Parallel, delayed

def flatten(matrix):
    return [item for i in tqdm(matrix) for item in i]

def perData_process(xml_file,ns):
    tree = ET.parse(xml_file)
    root = tree.getroot()
    perDataProcess = []

    for actSummary in root.findall('act:activities-summary',ns):
        for edu in actSummary.findall('act:educations',ns):
            for eduAffiliationGroup in edu.findall('act:affiliation-group',ns):
                for eduSummary in eduAffiliationGroup.findall('edu:education-summary',ns):
                    eduStartDate = 0
                    eduOrgName = eduOrgCity = eduOrgCountry = eduOrgRegion = None

                    for eduStartDateElement in eduSummary.findall('com:start-date',ns):
                        for eduStartDateYearElement in eduStartDateElement.findall('com:year',ns):
                            eduStartDate += 10000 * int(eduStartDateYearElement.text)
                        for eduStartDateMonthElement in eduStartDateElement.findall('com:month',ns):
                            eduStartDate += 100 * int(eduStartDateMonthElement.text)
                        for eduStartDateDayElement in eduStartDateElement.findall('com:day',ns):
                            eduStartDate += int(eduStartDateDayElement.text)

                    for eduOrg in eduSummary.findall('com:organization',ns):
                        eduOrgName = eduOrg.find('com:name',ns).text

                        for eduAddress in eduOrg.findall('com:address',ns):
                            eduOrgCity = eduAddress.find('com:city',ns).text
                            eduOrgCountry = eduAddress.find('com:country',ns).text

                            for eduOrgRegionElement in eduAddress.findall('com:region',ns):
                                eduOrgRegion = eduOrgRegionElement.text

                    if eduStartDate != 0 and eduOrgName is not None:
                        perDataProcess.append({'StartDate': eduStartDate,
                            'OrgName': eduOrgName, 'OrgCity': eduOrgCity, 'OrgRegion': eduOrgRegion, 'OrgCountry': eduOrgCountry})

        for emp in actSummary.findall('act:employments',ns):
            for empAffiliationGroup in emp.findall('act:affiliation-group',ns):
                for empSummary in empAffiliationGroup.findall('emp:employment-summary',ns):
                    empStartDate = 0
                    empOrgName = empOrgCity = empOrgRegion = empOrgCountry = None

                    for empStartDateElement in empSummary.findall('com:start-date',ns):
                        for empStartDateYearElement in empStartDateElement.findall('com:year',ns):
                            empStartDate += 10000 * int(empStartDateYearElement.text)
                        for empStartDateMonthElement in empStartDateElement.findall('com:month',ns):
                            empStartDate += 100 * int(empStartDateMonthElement.text)
                        for empStartDateDayElement in empStartDateElement.findall('com:day',ns):
                            empStartDate += int(empStartDateDayElement.text)

                    for empOrg in empSummary.findall('com:organization',ns):
                        empOrgName = empOrg.find('com:name',ns).text

                        for empAddress in empOrg.findall('com:address',ns):
                            empOrgCity = empAddress.find('com:city',ns).text
                            empOrgCountry = empAddress.find('com:country',ns).text

                            for empOrgRegionElement in empAddress.findall('com:region',ns):
                                empOrgRegion = empOrgRegionElement.text

                    if empStartDate != 0 and empOrgName is not None:
                        perDataProcess.append({'StartDate': empStartDate,
                            'OrgName': empOrgName, 'OrgCity': empOrgCity, 'OrgRegion': empOrgRegion, 'OrgCountry': empOrgCountry})

    return perDataProcess

def perData_proc_batch(batch,ns):
  return [perData_process(xml_file,ns)
    for xml_file in tqdm(batch)]

def perData_batch_file(array,n_workers):
  file_len = len(array)
  batch_size = round(file_len / n_workers)
  batches = [array[ix : ix + batch_size]
    for ix in tqdm(range(0,file_len,batch_size))]
  return batches

def dataFlow_sortDate(x):
    return x['StartDate']

def dataFlow_process(perDataElement):
    perDataOrgName = []
    dataFlowProcess = []
    
    lenPerDataElement = len(perDataElement)
    for x in tqdm(range(lenPerDataElement)):
        perDataElementX = perDataElement[x]

        lenPerDataElementX = len(perDataElement[x])
        for y in range(1,lenPerDataElementX):
            ori = perDataElementX[y-1]
            des = perDataElementX[y]
    
            dataFlowOrigin = ori['OrgName']
            dataFlowDestination = des['OrgName']
            dataFlowName = dataFlowOrigin + ' -> ' + dataFlowDestination

            if perDataOrgName.count(dataFlowName) == 0:
                perDataOrgName.append(dataFlowName)
                dataFlowProcess.append(
                    {'Count': 1, 'OrgFlow': dataFlowName, 'OriOrgName': dataFlowOrigin, 'DesOrgName': dataFlowDestination,
                    'OriCity': ori['OrgCity'], 'DesCity': des['OrgCity'], 
                    'OriRegion': ori['OrgRegion'], 'DesRegion': des['OrgRegion'], 
                    'OriCountry': ori['OrgCountry'], 'DesCountry': des['OrgCountry']})
            else:
                i = perDataOrgName.index(dataFlowName)
                dataFlowProcess[i]['Count'] = dataFlowProcess[i]['Count'] + 1

    return dataFlowProcess

def dataFlow_batch_file(array,n_workers):
  file_len = len(array)
  batch_size = round(file_len / n_workers)
  batches = [array[ix : ix + batch_size]
    for ix in tqdm(range(0,file_len,batch_size))]
  return batches

def dataFlow_sortOrgFlow(x):
    return x['OrgFlow']

def dataCount_process(dataFlowElement):
    dataFlowOrgName = []
    dataCountProcess = []

    for x in tqdm(dataFlowElement):
        oriOrgName = x['OriOrgName']
        desOrgName = x['DesOrgName']
        xCount = x['Count']

        i1 = dataFlowOrgName.count(oriOrgName) == 0
        i2 = dataFlowOrgName.count(desOrgName) == 0

        if i1 and i2:
            if oriOrgName == desOrgName:
                dataFlowOrgName.append(oriOrgName)
                dataCountProcess.append({'OrgName': oriOrgName, 'City': x['OriCity'], 'Region': x['OriRegion'], 'Country': x['OriCountry'], 'In': 0, 'Out': 0, 'Self': xCount})
            else:
                dataFlowOrgName.append(oriOrgName)
                dataFlowOrgName.append(desOrgName)
                dataCountProcess.append({'OrgName': oriOrgName, 'City': x['OriCity'], 'Region': x['OriRegion'], 'Country': x['OriCountry'], 'In': 0, 'Out': xCount, 'Self': 0})
                dataCountProcess.append({'OrgName': desOrgName, 'City': x['DesCity'], 'Region': x['DesRegion'], 'Country': x['DesCountry'], 'In': xCount, 'Out': 0, 'Self': 0})

        elif (i1 or i2) is not True:
            if oriOrgName == desOrgName:
                dataCountProcess[dataFlowOrgName.index(oriOrgName)]['Self'] += xCount
            else:
                dataCountProcess[dataFlowOrgName.index(desOrgName)]['In'] += xCount
                dataCountProcess[dataFlowOrgName.index(oriOrgName)]['Out'] += xCount

        elif i1:
            dataFlowOrgName.append(oriOrgName)
            dataCountProcess[dataFlowOrgName.index(desOrgName)]['In'] += xCount
            dataCountProcess.append({'OrgName': oriOrgName, 'City': x['OriCity'], 'Region': x['OriRegion'], 'Country': x['OriCountry'], 'In': 0, 'Out': xCount, 'Self': 0})
        else:
            dataFlowOrgName.append(desOrgName)
            dataCountProcess[dataFlowOrgName.index(oriOrgName)]['Out'] += xCount
            dataCountProcess.append({'OrgName': desOrgName, 'City': x['DesCity'], 'Region': x['DesRegion'], 'Country': x['DesCountry'], 'In': xCount, 'Out': 0, 'Self': 0})

    return dataCountProcess

def dataCount_batch_file(array,n_workers):
  file_len = len(array)
  batch_size = round(file_len / n_workers)
  batches = [array[ix : ix + batch_size]
    for ix in tqdm(range(0,file_len,batch_size))]
  return batches

def dataCount_sortDate(x):
    return x['OrgName']

if __name__ == '__main__':
    directory_path = "D:/ORCID_2023_10_summaries"
    xml_files = glob.glob(directory_path + "/*/*.xml")

    max_workers = 2 * mp.cpu_count()
    preDataLen = len(xml_files)
    n_workers = preDataLen if max_workers > preDataLen else max_workers

    print(f"{n_workers} workers are available")

    ns = {'com':'http://www.orcid.org/ns/common',
        'act':'http://www.orcid.org/ns/activities',
        'edu':'http://www.orcid.org/ns/education',
        'emp':'http://www.orcid.org/ns/employment'}

    perData = Parallel(n_jobs=n_workers,backend="multiprocessing")(delayed(perData_proc_batch)(batch,ns)
        for batch in tqdm(perData_batch_file(xml_files,n_workers)))

    perDataFlatten = [x for x in flatten(perData) if x]
    perDataFlattenLen = len(perDataFlatten)
    for i in range(perDataFlattenLen):
        perDataFlatten[i].sort(key = dataFlow_sortDate)
        
    print('Stage 0 cleared')

    max_workers = 2 * mp.cpu_count()
    n_workers = perDataFlattenLen if max_workers > perDataFlattenLen else max_workers

    print(f"{n_workers} workers are available")
    
    dataFlow = Parallel(n_jobs=n_workers,backend="multiprocessing")(delayed(dataFlow_process)(batch)
        for batch in tqdm(dataFlow_batch_file(perDataFlatten,n_workers)))
    
    dataFlowFlatten = [x for x in flatten(dataFlow) if x]
    dataFlowFlatten.sort(key = dataFlow_sortOrgFlow)

    x = 1
    lenDataFlow = len(dataFlowFlatten)
    with tqdm(total = lenDataFlow - 1) as pbar:
        while x < lenDataFlow:
            pbar.update(1)
            i = dataFlowFlatten[x]

            if dataFlowFlatten[x-1]['OrgFlow'] == i['OrgFlow']:
                dataFlowFlatten[x-1]['Count'] += i['Count']
                del dataFlowFlatten[x]
                lenDataFlow -= 1
            else:
                x += 1

    df = pd.DataFrame(dataFlowFlatten)
    output_file = os.path.join(directory_path, "dataFlow.csv")
    df.to_csv(output_file,index=False,encoding='utf-8-sig')

    print(df)
    print("Data exported to", output_file)
    print('Stage 1 cleared')

    max_workers = 2 * mp.cpu_count()
    preDataLen = len(dataFlowFlatten)
    n_workers = preDataLen if max_workers > preDataLen else max_workers

    print(f"{n_workers} workers are available")

    dataCount = Parallel(n_jobs=n_workers,backend="multiprocessing")(delayed(dataCount_process)(batch)
        for batch in tqdm(dataCount_batch_file(dataFlowFlatten,n_workers)))

    dataCountFlatten = [x for x in flatten(dataCount) if x]
    dataCountFlatten.sort(key = dataCount_sortDate)

    x = 1
    lenDataCount = len(dataCountFlatten)
    with tqdm(total = lenDataCount - 1) as pbar:
        while x < lenDataCount:
            pbar.update(1)
            i = dataCountFlatten[x]

            if dataCountFlatten[x-1]['OrgName'] == i['OrgName']:
                dataCountFlatten[x-1]['In'] += i['In']
                dataCountFlatten[x-1]['Out'] += i['Out']
                dataCountFlatten[x-1]['Self'] += i['Self']
                del dataCountFlatten[x]
                lenDataCount -= 1
            else:
                x += 1

    df = pd.DataFrame(dataCountFlatten)
    output_file = os.path.join(directory_path, "dataCount.csv")
    df.to_csv(output_file,index=False,encoding='utf-8-sig')

    print(df)
    print("Data exported to", output_file)
    print('Stage 2 cleared')