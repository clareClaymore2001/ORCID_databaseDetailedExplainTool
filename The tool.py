import os
import xml.etree.ElementTree as ET
import pandas as pd
import glob
import xlsxwriter

# Set the directory path
directory_path = "D:/ORCID_2023_10_summaries/0000"

# Get a list of all XML files in the directory
xml_files = glob.glob(directory_path + "/*.xml")

# Create a list to store the data
data = []
perData = []
perDataCount = 0
perDataLen = len(xml_files)
ns = {'com':'http://www.orcid.org/ns/common',
        'act':'http://www.orcid.org/ns/activities',
        'edu':'http://www.orcid.org/ns/education',
        'emp':'http://www.orcid.org/ns/employment'}

def sortDate(x):
    return x['StartDate']

# Iterate over each XML file
for xml_file in xml_files:
    perDataCount += 1
    perDataPath = perDataCount * 100000000

    # Parse the XML data file
    tree = ET.parse(xml_file)
    root = tree.getroot()

    for actSummary in root.findall('act:activities-summary',ns):
        for edu in actSummary.findall('act:educations',ns):
            for eduAffiliationGroup in edu.findall('act:affiliation-group',ns):
                for eduSummary in eduAffiliationGroup.findall('edu:education-summary',ns):
                    eduStartDate = perDataPath
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

                    if eduStartDate != perDataPath and eduOrgName is not None:
                        perData.append({'Count':perDataCount, 'StartDate': eduStartDate, 'OrgName': eduOrgName, 'OrgCity': eduOrgCity, 'OrgRegion': eduOrgRegion, 'OrgCountry': eduOrgCountry})
                        print(perDataLen, perDataCount, eduOrgName)

        for emp in actSummary.findall('act:employments',ns):
            for empAffiliationGroup in emp.findall('act:affiliation-group',ns):
                for empSummary in empAffiliationGroup.findall('emp:employment-summary',ns):
                    empStartDate = perDataPath
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

                    if empStartDate != perDataPath and empOrgName is not None:
                        perData.append({'Count':perDataCount, 'StartDate': empStartDate, 'OrgName': empOrgName, 'OrgCity': empOrgCity, 'OrgRegion': empOrgRegion, 'OrgCountry': empOrgCountry})
                        print(perDataLen, perDataCount, empOrgName)

perData.sort(key = sortDate)

perDataCount = 0
lenPreData = len(perData)
for x in range(1, lenPreData):
    perDataCount += 1
    ori = perData[x-1]
    des = perData[x]
    
    if ori['Count'] == des['Count']:
        dataFlowOrigin = ori['OrgName']
        dataFlowDestination = des['OrgName']
        dataCount = False

        lenData = len(data)
        for i in range(0, lenData):
            if data[i]['OriOrgName'] == dataFlowOrigin and data[i]['DesOrgName'] == dataFlowDestination:
                dataCount = data[i]['Count'] = data[i]['Count'] + 1
                print(lenPreData, perDataCount, des['OrgName'])
                break
                
        if dataCount is False:
            data.append({'Count': 1, 'OriOrgName': dataFlowOrigin, 'DesOrgName': dataFlowDestination,
                        'OriCity': ori['OrgCity'], 'DesCity': des['OrgCity'], 
                        'OriRegion': ori['OrgRegion'], 'DesRegion': des['OrgRegion'], 
                        'OriCountry': ori['OrgCountry'], 'DesCountry': des['OrgCountry']})

# Create a DataFrame from the data
df = pd.DataFrame(data)

# Specify the output file path
output_file = os.path.join(directory_path, "Axway_Accounts.xlsx")

# Create a Pandas Excel writer using xlsxwriter as the engine
writer = pd.ExcelWriter(output_file, engine='xlsxwriter')

# Write the DataFrame to the Excel file
df.to_excel(writer, index=False, sheet_name='Sheet1')

# Get the xlsxwriter workbook and worksheet objects
workbook = writer.book
worksheet = writer.sheets['Sheet1']

# Iterate over the columns and adjust the widths based on content
for i, column in enumerate(df.columns):
    # Find the maximum length of the cells in the column
    column_width = max(df[column].astype(str).map(len).max(), len(column)) + 2
    # Set the width of the column
    worksheet.set_column(i, i, column_width)

# Save and close the workbook
writer.close()

print("Data exported to", output_file)

dataFinal = []
DataCount = 0
lenData = len(data)
for x in range(0, lenData):
    DataCount += 1
    dataCount = 0
    dataElement = data[x]
    oriOrgName = dataElement['OriOrgName']
    desOrgName = dataElement['DesOrgName']
    dataElementCount = dataElement['Count']

    lenDataFinal = len(dataFinal)
    for i in range(0, lenDataFinal):
        i1 = dataFinal[i]['OrgName'] == oriOrgName
        i2 = dataFinal[i]['OrgName'] == desOrgName

        if i1 and i2:
            dataFinal[i]['Self'] += dataElementCount
            dataCount = 3
            print(lenData, DataCount, oriOrgName)
            break

        elif i1:
            dataFinal[i]['Out'] += dataElementCount
            if dataCount == 0:
                dataCount = 1
            else:
                dataCount = 3
                print(lenData, DataCount, oriOrgName)
                break

        elif i2:
            dataFinal[i]['In'] += dataElementCount
            if dataCount == 0:
                dataCount = 2
            else:
                dataCount = 3
                print(lenData, DataCount, desOrgName)
                break

    if dataCount != 3:
        if dataCount == 0:
            if oriOrgName == desOrgName:
                dataFinal.append({'OrgName': oriOrgName, 'City': dataElement['OriCity'], 'Region': dataElement['OriRegion'], 'Country': dataElement['OriCountry'], 'In': 0, 'Out': 0, 'Self': dataElementCount})
            else:
                dataFinal.append({'OrgName': desOrgName, 'City': dataElement['DesCity'], 'Region': dataElement['DesRegion'], 'Country': dataElement['DesCountry'], 'In': dataElementCount, 'Out': 0, 'Self': 0})
                dataFinal.append({'OrgName': oriOrgName, 'City': dataElement['OriCity'], 'Region': dataElement['OriRegion'], 'Country': dataElement['OriCountry'], 'In': 0, 'Out': dataElementCount, 'Self': 0})

        elif dataCount == 1:
            dataFinal.append({'OrgName': desOrgName, 'City': dataElement['DesCity'], 'Region': dataElement['DesRegion'], 'Country': dataElement['DesCountry'], 'In': dataElementCount, 'Out': 0, 'Self': 0})

        elif dataCount == 2:
            dataFinal.append({'OrgName': oriOrgName, 'City': dataElement['OriCity'], 'Region': dataElement['OriRegion'], 'Country': dataElement['OriCountry'], 'In': 0, 'Out': dataElementCount, 'Self': 0})

# Create a DataFrame from the data
df = pd.DataFrame(dataFinal)

# Specify the output file path
output_file = os.path.join(directory_path, "Axway_Accounts_2.xlsx")

# Create a Pandas Excel writer using xlsxwriter as the engine
writer = pd.ExcelWriter(output_file, engine='xlsxwriter')

# Write the DataFrame to the Excel file
df.to_excel(writer, index=False, sheet_name='Sheet1')

# Get the xlsxwriter workbook and worksheet objects
workbook = writer.book
worksheet = writer.sheets['Sheet1']

# Iterate over the columns and adjust the widths based on content
for i, column in enumerate(df.columns):
    # Find the maximum length of the cells in the column
    column_width = max(df[column].astype(str).map(len).max(), len(column)) + 2
    # Set the width of the column
    worksheet.set_column(i, i, column_width)

# Save and close the workbook
writer.close()

print("Data exported to", output_file)