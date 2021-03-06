# -*- coding: utf-8 -*-
"""am_fuzzy_clustering_primera_parte.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1f4qQXxgw7UXl2bXSPgAaIjD_22Y_WWsr
"""

from google.colab import drive
drive.mount('/content/project')

!pip install xlsxwriter

import numpy as np
import pandas as pd
from sklearn.datasets import load_iris
from sklearn import preprocessing
from sklearn.metrics import f1_score
from sklearn.metrics.cluster import adjusted_rand_score
from openpyxl import Workbook, load_workbook
from openpyxl.drawing.image import Image
from openpyxl.utils.dataframe import dataframe_to_rows
import random
import time
import datetime
from datetime import datetime
import pprint
import xlsxwriter

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

#Declare global variables
#K
PROTOTYPE_LIMIT = 10
#n
DISTANCES_MATRIX_SIZE = 2000
#Q
CARDINALITY = 2
#P
NUMBER_OF_MATRIXES = 3 
#M
M_VALUE = 1.6
#ITERATIONS
T = 150
T_TIMES = 100
#s
s = 1
#Error
e = 10e-10 #(Error value)

#Get normalized dataset (Distances matrix)

def getDistancesMatrix3D(m1,m2,m3):
    return np.stack((m1,m2,m3))

#Read CSV matrices
DISTANCES_MATRIX_FEAT = pd.read_csv('/content/project/My Drive/Machine Learning - Revenant/Prof. Francisco de Assis Module/Datasets/kian_100_iterations/feat.csv', sep=' ', index_col=0)
DISTANCES_MATRIX_FOURIER = pd.read_csv('/content/project/My Drive/Machine Learning - Revenant/Prof. Francisco de Assis Module/Datasets/kian_100_iterations/fourier_z.csv', sep=',', index_col=0)
DISTANCES_MATRIX_KAR = pd.read_csv('/content/project/My Drive/Machine Learning - Revenant/Prof. Francisco de Assis Module/Datasets/kian_100_iterations/kar.csv', sep=' ', index_col=0)

#Get 2000x2000 matrix from each matrix 
matrix1 = DISTANCES_MATRIX_FEAT.values
matrix2 = DISTANCES_MATRIX_FOURIER.values
matrix3 = DISTANCES_MATRIX_KAR.values

print("DISTANCES_MATRIX_FEAT (1ra matrix)")
print(DISTANCES_MATRIX_FEAT.values.shape)
print("DISTANCES_MATRIX_FOURIER (2ra matrix)")
print(DISTANCES_MATRIX_FOURIER.values.shape)
print("DISTANCES_MATRIX_KAR (3ra matrix)")
print(DISTANCES_MATRIX_KAR.values.shape)

#Stack 3 matrices to 1 3D Matrix
D = getDistancesMatrix3D(matrix1, matrix2, matrix3)
print("D size: ",D.shape)

#UTILS
#------ RANDOM PROTOTYPES ------
def getRandomCardinalityPrototypes(prototypeSize, matrixSize, cardinality):
    randomPrototypes = np.random.choice(matrixSize, prototypeSize*cardinality, replace=False)
    randomPrototypes = np.split(randomPrototypes, cardinality)
    return np.array(randomPrototypes)   

def setArrayToCardinalPrototypes(arrayPrototypes, q):
    prototypesArray = np.zeros(shape=( q, int(arrayPrototypes.size/q) ))
    row = 0
    column = 0
    for i in range(arrayPrototypes.size):
        if(row > q-1 ):
            row = 0
            column = column + 1
        prototypesArray[row][column] = arrayPrototypes[i]
        row = row + 1
    return prototypesArray

# ITERATIONS
def concatenateMatrixToArray(array,matrix):
    if len(array) == 0:
        array = matrix[None]
    else:
        array=np.vstack((array,matrix[None]))
    return array

# MATRIX UIK METHOD
def getMembershipDegreeMatrix(prototypes,lambdaMatrix):
    K = PROTOTYPE_LIMIT
    n = DISTANCES_MATRIX_SIZE
    q = CARDINALITY
    m = M_VALUE
    p = NUMBER_OF_MATRIXES    
    matricesMerge = mergeAllMatrices(D)    
    #Start Uik matrix with ceros
    u = np.zeros((n,K))
    for i in range(n):
        for k in range(K): 
            e_gk = getPrototypeIndexes(prototypes,k,q)
            uik_result = 0
            for h in range(K): 
                e_gh = getPrototypeIndexes(prototypes,h,q) 
                num = 0
                den = 0
                for j in range(p):
                    num += (lambdaMatrix[k,j]**s)*np.sum(matricesMerge[i,e_gk])
                    den += (lambdaMatrix[h,j]**s)*np.sum(matricesMerge[i,e_gh])
                uik_result += (num/den)**(1/(m-1))                
            u[i,k] = uik_result**(-1)
    return u.transpose()  

#----***UTILS***-------
#returns 2 matrix points [row1,row2]   
def getPrototypeIndexes(prototypes,position,q):
    gk = np.array([])
    for i in range(q):
        gk = np.append(gk,prototypes[i][position])
    return gk.astype(int)   

#If matrix sent, (3,2000,2000) : returns matrix sum (2000,2000)
def mergeAllMatrices(matrix):
    return matrix.sum(axis=0)

#Get prototype rows from matrix according to prototype array and cardinality
# prototypes (2x20) , returns matrix (10x2000) (each row was summed previosly)
def getCardinalityMatrix(matrix,prototypesArray,cardinality):    
    cardinalityMatrix = np.zeros((PROTOTYPE_LIMIT,DISTANCES_MATRIX_SIZE))
    for i in range(cardinality):
        prototypeMatrix = matrix[prototypesArray[i],:]
        cardinalityMatrix = cardinalityMatrix + prototypeMatrix
    return cardinalityMatrix

#OBJECTIVE FUNCTION METHOD
def getObjectiveMatrix(prototypes,uikMatrix,weights):
        
    K = PROTOTYPE_LIMIT
    n = DISTANCES_MATRIX_SIZE
    q = CARDINALITY
    m = M_VALUE
    p = NUMBER_OF_MATRIXES
    
    #Prototype Points form Matrix
    uikMatrix = np.power(uikMatrix, m) #10x2000 Uik(^2)
        
    #Get distances from prototypes
    proto_feat_matrix = getCardinalityMatrix(DISTANCES_MATRIX_FEAT.values,prototypes,q ) #10x2000 (1ra)
    proto_fourier_matrix = getCardinalityMatrix(DISTANCES_MATRIX_FOURIER.values,prototypes,q )#10x2000 (2da)
    proto_kar_matrix = getCardinalityMatrix(DISTANCES_MATRIX_KAR.values,prototypes,q ) #10x2000 (3ra)
    
    for i in range(K):
        proto_feat_matrix[i,:] = proto_feat_matrix[i,:] * weights[i,0]
        proto_fourier_matrix[i,:] = proto_fourier_matrix[i,:] * weights[i,1]
        proto_kar_matrix[i,:] = proto_kar_matrix[i,:] * weights[i,2]
    
    sumOfMatrixes = proto_feat_matrix + proto_fourier_matrix + proto_kar_matrix
    objMatrix = uikMatrix * sumOfMatrixes
    return objMatrix

#----***UTILS***-------
def getPrototypePointsMatrix(prototypes,matrix):
    rowSize = PROTOTYPE_LIMIT
    columnSize = DISTANCES_MATRIX_SIZE
    prototypeMatrix = np.zeros(shape=(rowSize,columnSize)) 
    for i in range(rowSize):
        prototypeMatrix[i] = matrix[ prototypes[i] ]
    return prototypeMatrix

#NEW PROTOTYPES METHOD
def getNewPrototypesMINValue(uikMatrix, weights): 
    
    K = PROTOTYPE_LIMIT
    q = CARDINALITY
    m = M_VALUE
    
    #Get distances from prototypes
    m1 = np.copy(DISTANCES_MATRIX_FEAT.values)
    m2 = np.copy(DISTANCES_MATRIX_FOURIER.values)
    m3 = np.copy(DISTANCES_MATRIX_KAR.values)
    #Prototype Points form Matrix
    uikMatrix = np.power(uikMatrix, m)
    newPrototypes = np.array([])
    j0 = 0
    j1 = 1
    j2 = 2
            
    for k in range(K): # 1 - 10      
        kM1 = m1 * weights[k,j0] # k = 0 ; j0 = 0 weights[0][0] =1
        kM2 = m2 * weights[k,j1] # k = 0 ; j1 = 1 weights[0][1] =1
        kM3 = m3 * weights[k,j2] # k = 0 ; j2 = 1 weights[0][2] =1
        kSum = kM1 + kM2  + kM3
        #Multiply Uik (k index row) x All rows from matrix kSum
        kSum = np.multiply(kSum, uikMatrix[k])
        kSumRows = np.sum(kSum, axis=1) # 1 x 2000
        minValueFromMatrix = np.sort(kSumRows.flatten())[:q] # First 2 min Values from sorted array
        minIndexFromMatrix = np.argsort(kSumRows.flatten())[:q] # First 2 min Ixdex from sorted array   
        newPrototypes = np.append(newPrototypes,minIndexFromMatrix) # 2 new prototypes, total = 20
    
    return setArrayToCardinalPrototypes(newPrototypes,q).astype(int)

#WEIGHTS
def getWeightMatrix(prototypes, uikMatrix):
    
    K = PROTOTYPE_LIMIT
    n = DISTANCES_MATRIX_SIZE
    q = CARDINALITY
    m = M_VALUE
    p = NUMBER_OF_MATRIXES
    #Get the "prototypes" array points from matrixes (m1,m2,m3)
    m1 = getCardinalityMatrix(DISTANCES_MATRIX_FEAT.values,prototypes,q )
    m2 = getCardinalityMatrix(DISTANCES_MATRIX_FOURIER.values,prototypes,q )
    m3 = getCardinalityMatrix(DISTANCES_MATRIX_KAR.values,prototypes,q )
    #Prototype Points form Matrix
    uikMatrix = np.power(uikMatrix, m)
    # Weight Matrix (3 x 10)
    weightMatrix = np.zeros(shape=(PROTOTYPE_LIMIT,NUMBER_OF_MATRIXES)) 
    for k in range(PROTOTYPE_LIMIT):
        
        m1[k,:] = np.multiply(m1[k,:],uikMatrix[k,:])
        m2[k,:] = np.multiply(m2[k,:],uikMatrix[k,:])
        m3[k,:] = np.multiply(m3[k,:],uikMatrix[k,:])
        
        dividend = np.sum(m1[k,:]) * np.sum(m2[k,:]) * np.sum(m3[k,:])
        dividend = pow( dividend , (1/p) )
        
        weightMatrix[k][0] = dividend/np.sum(m1[k,:])
        weightMatrix[k][1] = dividend/np.sum(m2[k,:])
        weightMatrix[k][2] = dividend/np.sum(m3[k,:])
                            
    return weightMatrix

#ITERATION CERO

randomRowSampleValues = np.array([])
initU = np.array([])
initObjectiveMatrix = np.array([])
initTotalSumObjectiveMatrix = np.array([])
initNewPrototypesArray = np.array([])
#We do not need weights for the first iteration
initWeights = np.ones((10,3))

def runIterationCero(initPrototypes):
    
    global randomRowSampleValues 
    global initU 
    global initObjectiveMatrix 
    global initTotalSumObjectiveMatrix
    global initNewPrototypesArray
    global initWeights
    
    #START UIK
    initU = getMembershipDegreeMatrix(initPrototypes,initWeights)
    #START OBJECTVIVE FUNCTION
    initObjectiveMatrix = getObjectiveMatrix(initPrototypes,initU, initWeights)
    #STAR TOTAL SUM OF OBJECTIVE MATRIX
    initTotalSumObjectiveMatrix = np.sum(initObjectiveMatrix)
    #START NEW PROTOTYPES
    initNewPrototypesArray = getNewPrototypesMINValue(initU, initWeights)
    #START WEIGHTS
    initWeights = getWeightMatrix(initNewPrototypesArray,initU)
    
    print(bcolors.HEADER + "LAUNCH: (T = 0) 1 / "+ str(T) + bcolors.HEADER)
    print("T=0 Uik")
    print(initU[0])
    print("T=0 Uik Column's Sum")
    print(initU.sum(axis=0))
    print("T=0 objectiveMatrix")
    print(initObjectiveMatrix)
    print("T=0 Total sum objectiveMatrix")
    print(initTotalSumObjectiveMatrix)
    print("T=0 New prototypes(array)")
    print(initNewPrototypesArray)

#CRISP PARTITION
def getCrispPartition( uikSelected ):
    #Generate original class indicators [0:0,1:0,2:0....1998:9,1999:9]
    originalClassList = generateOriginalClasses()
    #Get maximum value from all columns of selected Uik
    maxColumnValues = np.argmax(uikSelected, axis=0)
    #Create empty dictionary. Here the key value will be the cluster number
    #e.g. 1 : [1,2,3,4,5] ; 2 : [6,7,8,9,10] ; 3: [11,12,13,14,15]....10:[1999,2000]
    crispDic = {}
    #Store the value in that point as key, index coordinate as value
    # e.g. value in position 1 is a 7, then cluster 7 has column 1 => 7 : [1] 
    for x in range(maxColumnValues.size): #[0 - 1999]
        if not maxColumnValues[x]+1 in crispDic:
            crispDic[ maxColumnValues[x]+1 ] = {} 
            crispDic[ maxColumnValues[x]+1 ]['points'] = np.array([],dtype=int)
        crispDic[ maxColumnValues[x]+1 ]['points'] = np.append(crispDic[ maxColumnValues[x]+1 ]['points'],x+1)
    
    #Get originalClasses
    clusteredDict = getOriginalClassType(crispDic,originalClassList)
    sortedDict = dict(sorted(clusteredDict[0].items()))
    sortedDict["clustering"] = sortAllClustersAccordingToPoints(sortedDict)
    sortedDict["error"] = clusteredDict[1]
    return sortedDict

def generateOriginalClasses():
  originalClass = np.zeros(DISTANCES_MATRIX_SIZE,dtype=int)
  minLim = 0
  maxLim = 200
  intervalRange = 200
  for number in range(PROTOTYPE_LIMIT): 
    originalClass[ minLim:maxLim ] = number
    minLim = maxLim
    maxLim = maxLim + intervalRange  
  return originalClass

def generateOriginalClassesTrueIndex():
  originalClass = np.zeros(DISTANCES_MATRIX_SIZE,dtype=int)
  minLim = 0
  maxLim = 200
  intervalRange = 200
  for number in range(PROTOTYPE_LIMIT): 
    originalClass[ minLim:maxLim ] = number +1
    minLim = maxLim
    maxLim = maxLim + intervalRange  
  return originalClass

def getOriginalClassType(crispDic,originalClasses):
  resultArray = np.array([])
  for key,elem in crispDic.items():
    counter = np.zeros(PROTOTYPE_LIMIT)
    for point in range(elem['points'].size): 
      dictPoint = elem['points'][point]        
      originalType = originalClasses[dictPoint-1]
      counter[originalType] = counter[originalType]+1
    maxClusterValue = np.argmax(counter)
    crispDic[key]['cluster'] = maxClusterValue + 1
    crispDic[key]['counter_cluster'] = counter
  
  resultArray = np.append(resultArray,crispDic)
  finalError = calculateCrispError(crispDic,originalClasses)
  resultArray = np.append(resultArray,finalError)
  return resultArray 

def calculateCrispError(crispDic,originalClasses):
  sumClassif_Error_Correct = 0
  sumClassif_Error_Incorrect = 0
  for key,elem in crispDic.items():
    for point in range(elem['points'].size): 
      dictPoint = elem['points'][point]        
      originalType = originalClasses[dictPoint-1]
      if (int(elem['cluster']) == originalType+1):
        sumClassif_Error_Correct += 1
      else:
        sumClassif_Error_Incorrect += 1
  print("sumClassif_Error_Correct: ",sumClassif_Error_Correct)
  print("sumClassif_Error_Incorrect: ",sumClassif_Error_Incorrect)
  print("Error: ",(sumClassif_Error_Incorrect*100)/DISTANCES_MATRIX_SIZE,"%")
  return (sumClassif_Error_Incorrect*100)/DISTANCES_MATRIX_SIZE    

def sortAllClustersAccordingToPoints(crispDic):
  sortedArray = np.zeros(DISTANCES_MATRIX_SIZE, dtype=int)
  for key,elem in crispDic.items():
      for i in range(elem['points'].size):
        point = elem['points'][i]
        sortedArray[point-1] = elem['cluster']
  return sortedArray

def getPartitionCoefficient(uikMatrix):
  K = PROTOTYPE_LIMIT
  n = DISTANCES_MATRIX_SIZE
  uik_square = np.power(uikMatrix, 2)
  VPC = np.sum(uik_square) / n
  VMPC = 1 - (K/(K-1))*(1-VPC)
  return VMPC

def getPatitionEntropy(ukMatrix):
  K = PROTOTYPE_LIMIT
  n = DISTANCES_MATRIX_SIZE
  ulog = np.log(ukMatrix)
  uprod = ulog*ukMatrix
  VPE = -np.sum(uprod) / n
  return VPE

def getF_measure(y_predict, average):
  y_true = generateOriginalClassesTrueIndex()
  return f1_score(y_true, y_predict, average=average)

def getAdjustedRand(y_predict):
  y_true = generateOriginalClassesTrueIndex()
  return adjusted_rand_score(y_true, y_predict)

#Method to repeat 150 times Fuzzy k-medoids algorithm
def iterateFuzzyKMedoids(prototypes,weights,lastJ):
    kMedoidsResult = {}
    iterations = 1
    nextJ = lastJ 
    e = pow(10,-10)
    for t in range(T-1):
        print(bcolors.OKBLUE + "LAUNCH: T = " + str(iterations + 1) + " / "+ str(T) + bcolors.OKBLUE)
        print("------ > Starting Prototypes: ",iterations)
        print(prototypes)
        #Uik Matrix
        newUik = getMembershipDegreeMatrix(prototypes,weights)
        newObjectiveMatrix = getObjectiveMatrix(prototypes,newUik, weights)
        sumNewObjectiveMatrix = np.sum(newObjectiveMatrix)
        print("------ > Objective Matrix Sum: ",iterations)
        print(np.sum(newObjectiveMatrix))
        #New Prototypes
        prototypes = getNewPrototypesMINValue(newUik, weights)
        print("------ > New Prototypes: ",iterations)
        print(prototypes)
        weights = getWeightMatrix(prototypes,newUik)
        #Set result dictionary
        crispPartition = getCrispPartition(newUik)
        kMedoidsResult["prototype"] = prototypes
        kMedoidsResult["uik"] = newUik
        kMedoidsResult["J"] = sumNewObjectiveMatrix
        kMedoidsResult["crisp"] = crispPartition
        kMedoidsResult["VMPC"] = getPartitionCoefficient(newUik)
        kMedoidsResult["VPE"] = getPatitionEntropy(newUik)
        kMedoidsResult["Fmacro"] = getF_measure(crispPartition["clustering"],'macro')
        kMedoidsResult["Fmicro"] = getF_measure(crispPartition["clustering"],'micro')
        kMedoidsResult["Fweighted"] = getF_measure(crispPartition["clustering"],'weighted')
        kMedoidsResult["AdjustedRand"] = getAdjustedRand(crispPartition["clustering"])
        #Update J
        lastJ = nextJ
        nextJ = sumNewObjectiveMatrix
        print("------ > J Value from Iteration: ",iterations-1)
        print(lastJ)
        print("------ > J Value from current Iteration: ",iterations)
        print(nextJ)
        #END CONDITION
        if (abs(nextJ - lastJ) <= e or iterations == T):
            print(bcolors.OKGREEN + "Condition abs{[J(t)] - [J(t-1)] is satisfied:" + bcolors.OKGREEN)
            print("------ > Jt - Jt-1 <= e: ",abs(nextJ - lastJ)," < ",e)                    
            break    
        iterations = iterations + 1
    return kMedoidsResult

#EXCEL SHEET CONFIGURATION

workbook = None
worksheet = None
cell_format = None
bold = None
Runsheet = None

def setupExcelSheet():
  global workbook
  global worksheet
  global cell_format
  global bold
  workbook = xlsxwriter.Workbook('run_ml_revenant.xlsx')
  worksheet = workbook.add_worksheet('Resume')
  worksheet.set_column('K:K', 13)
  worksheet.set_column('L:L', 13)
  worksheet.set_column('J:J', 11)
  worksheet.set_column('M:M', 50)
  #Bold
  bold = workbook.add_format({'align': 'center', 'valign': 'vcenter','bold': True})
  bold.set_text_wrap()
  bold.set_border()
  #Cell format
  cell_format = workbook.add_format({'align': 'center', 'valign': 'vcenter'})
  cell_format.set_text_wrap()
  cell_format.set_border()
  #Header
  worksheet.write('A1', 'Run', bold)
  worksheet.write('B1', 'Classification Error', bold)
  worksheet.write('C1', 'Objective Function (J)', bold)
  worksheet.write('D1', 'Modified partition coefficient [0-1]', bold)
  worksheet.write('E1', 'Partition entropy [0-2.3]', bold)
  worksheet.write('F1', 'F-measure_macro[0,1]', bold)
  worksheet.write('G1', 'F-measure_micro[0,1]', bold)
  worksheet.write('H1', 'F-measure_weighted[0,1]', bold)
  worksheet.write('I1', 'Adjusted Rand index [-1,1]', bold)
  worksheet.write('J1', 'Parameters', bold)
  worksheet.write('K1', 'Comp. time', bold)
  worksheet.write('L1', 'Data and time', bold)

def roundDecimal(num):
  return str(round(num,3))

def createExcelSheet(id,results):
  #Time Parameters
  time_elapsed = (time.perf_counter() - time_start0)
  minute = time_elapsed // 60
  seconds = time_elapsed % 60
  now = datetime.now()
  dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
  #POPULATE EXCEL SHEET
  worksheet.write('A'+str(id+2), id+1, cell_format)
  worksheet.write('B'+str(id+2), str(roundDecimal(results['crisp']['error']))+"%", cell_format)
  worksheet.write('C'+str(id+2), results['J'], cell_format)
  worksheet.write('D'+str(id+2), results['VMPC'], cell_format)
  worksheet.write('E'+str(id+2), results['VPE'], cell_format)
  worksheet.write('F'+str(id+2), roundDecimal(results['Fmacro']), cell_format)
  worksheet.write('G'+str(id+2), roundDecimal(results['Fmicro']), cell_format)
  worksheet.write('H'+str(id+2), roundDecimal(results['Fweighted']), cell_format)
  worksheet.write('I'+str(id+2), roundDecimal(results['AdjustedRand']), cell_format)
  worksheet.write('J'+str(id+2), "s ="+str(s)+"; m="+str(M_VALUE)+"; q="+str(CARDINALITY), cell_format)
  worksheet.write('K'+str(id+2), str(int(minute))+" min "+str(int(seconds))+" seg", cell_format)
  worksheet.write('L'+str(id+2), dt_string, cell_format)

def setupExcelRunSheet(id):
  global Runsheet
  Runsheet = workbook.add_worksheet('Launch ' + str(id+1))
  Runsheet.set_column('C:C', 60)
  Runsheet.set_column('B:B', 15)
  Runsheet.set_row(2, 70)
  Runsheet.set_row(3, 70)
  Runsheet.set_row(4, 70)
  Runsheet.write('A2', 'Cluster', bold)
  Runsheet.write('B2', 'Set - medoids(K - protótipos)', bold)
  Runsheet.write('C2', 'Lista de objetos da partição crisp de cada cluster', bold)
  Runsheet.write('D2', 'Total de objetos na partição crisp', bold)
  Runsheet.write('E2', 'Classe 1', bold)
  Runsheet.write('F2', 'Classe 2', bold)
  Runsheet.write('G2', 'Classe 3', bold)
  Runsheet.write('H2', 'Classe 4', bold)
  Runsheet.write('I2', 'Classe 5', bold)
  Runsheet.write('J2', 'Classe 6', bold)
  Runsheet.write('K2', 'Classe 7', bold)
  Runsheet.write('L2', 'Classe 8', bold)
  Runsheet.write('M2', 'Classe 9', bold)
  Runsheet.write('N2', 'Classe 10', bold)
  Runsheet.write('O2', 'Classe maior Votação crisp', bold)
  Runsheet.write('A3', 0, cell_format)
  Runsheet.write('A4', 1, cell_format)
  Runsheet.write('A5', 2, cell_format)
  Runsheet.write('A6', 3, cell_format)
  Runsheet.write('A7', 4, cell_format)
  Runsheet.write('A8', 5, cell_format)
  Runsheet.write('A9', 6, cell_format)
  Runsheet.write('A10', 7, cell_format)
  Runsheet.write('A11', 8, cell_format)
  Runsheet.write('A12', 9, cell_format)

def createExcelRunSheet(id,results):
  K = PROTOTYPE_LIMIT
  n = DISTANCES_MATRIX_SIZE
  q = CARDINALITY

  #Classe 0 - 9
  excelColumns = np.array(["E","F","G","H","I","J","K","L","M","N"])
  for i in range(K):
    protoString = ''
    crispString = ''
    pointString = '['
    sumPoints = 0
    sumClassCluster = 0
    clusterPopulate = 0
    crispKey = results["crisp"].get(i+1, "")
    crispCluster = crispKey.get("cluster", "") if crispKey  else ""
    #Populate Classes with cero
    for populate in range(K):
      Runsheet.write(excelColumns[populate]+str(i+3), sumClassCluster, cell_format)
    Runsheet.write('O'+str(i+3), str(clusterPopulate), cell_format)
    #Set - medoids(K - protótipos)
    for j in range(q):      
      crispString = " (Classe-"+str(crispCluster)+")" if crispCluster else ""
      protoString = protoString + str(results["prototype"][j][i])+crispString+"\n"
    #Lista de objetos da partição crisp de cada cluster
    #Total de objetos na partição crisp    
    if (crispKey):
      sumPoints = crispKey["points"].size
      for pt in range(crispKey["points"].size):
        pointString = pointString + str(crispKey["points"][pt])+","
      for cl in range(crispKey["counter_cluster"].size):
        sumClassCluster = crispKey["counter_cluster"][cl]
        Runsheet.write(excelColumns[cl]+str(i+3), sumClassCluster, cell_format)
      Runsheet.write('O'+str(i+3), str(crispCluster), cell_format)

    pointString = pointString + "]"    
    Runsheet.write('B'+str(i+3), protoString, cell_format)
    Runsheet.write('C'+str(i+3), pointString, cell_format)
    Runsheet.write('D'+str(i+3), sumPoints, cell_format)

#Repeat 100 times: Run algorithm FUzzy k-medoids 100 times (150 times each of them)
objJResults = np.array([])
uikResults = np.array([])
protoResults = np.array([])

setupExcelSheet()

for i in range(100):
    print(bcolors.ENDC + "" + bcolors.ENDC)
    print(bcolors.BOLD + "OUTLYING LAUNCH: " + str(i+1) + " / "+ str(T_TIMES) + bcolors.BOLD)
    time_start0 = time.perf_counter()
    randomRowSampleValues = getRandomCardinalityPrototypes(PROTOTYPE_LIMIT, DISTANCES_MATRIX_SIZE, CARDINALITY)
    print(bcolors.ENDC + "Random Prototypes:" + bcolors.ENDC)
    print(randomRowSampleValues)
    #Run iteration 0
    runIterationCero(randomRowSampleValues)
    #Get the results from 150 iterations
    results = iterateFuzzyKMedoids(initNewPrototypesArray,initWeights,initTotalSumObjectiveMatrix)
    print("RESULTS!!")
    print(results)
    #Store the results into 3 differente arrays and array of matrices
    objJResults = np.append(objJResults,results['J'])
    uikResults = concatenateMatrixToArray(uikResults,results['uik']) 
    protoResults = concatenateMatrixToArray(protoResults,results['prototype'])
    createExcelSheet(i,results)
    setupExcelRunSheet(i)  
    createExcelRunSheet(i,results)  

        
print("FINAL RESULTS (J)")
for j in range(100):
    print("Launch ",j+1,"=>",objJResults[j])

print("EXPORTING EXCEL FILE...")
workbook.close()
print("EXCEL FILE READY!")