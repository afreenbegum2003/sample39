import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import math
import warnings
warnings.filterwarnings("ignore")

"""# Pre-processing

### A bit of exploration
"""

feature_names=['Age (yrs)','Blood Pressure (mm/Hg)','Specific Gravity','Albumin','Sugar','Red Blood Cells',
               'Pus Cells','Pus Cell Clumps','Bacteria','Blood Glucose Random (mgs/dL)','Blood Urea (mgs/dL)',
               'Serum Creatinine (mgs/dL)','Sodium (mEq/L)','Potassium (mEq/L)','Hemoglobin (gms)','Packed Cell Volume',
               'White Blood Cells (cells/cmm)','Red Blood Cells (millions/cmm)','Hypertension','Diabetes Mellitus',
               'Coronary Artery Disease','Appetite','Pedal Edema','Anemia','Chronic Kidney Disease']
               
data=pd.read_csv("chronic_kidney_disease.csv", names = feature_names)

data.head()

"""We can see there are missing values.  
If their number is considerable, then we would have to be careful about which imputation technique to use.  
"""

data.info()

"""Many features are mistyped.  
Some features have quite a lot of missing values.  
One option is to drop them, but it's best to impute them with a decent imputation technique that preserves distributions, since we do not have many datapoints.
There are many techniques to choose.  
we will be using the KNNImputer from sklearn.
"""

data.describe()

"""You can see that some features have some serious outliers.  

---

### Data Cleaning

Let's deal with typos first.
"""

#Correcting some typos in the dataset
for i in range(data.shape[0]):
    if data.iloc[i,24]=='ckd\t':
        data.iloc[i,24]='ckd'
    if data.iloc[i,19] in [' yes','\tyes']:
        data.iloc[i,19]='yes'
    if data.iloc[i,19]=='\tno':
        data.iloc[i,19]='no'
    if data.iloc[i,20]=='\tno':
        data.iloc[i,20]='no'
    if data.iloc[i,15]=='\t?':
        data.iloc[i,15]=np.nan
    if data.iloc[i,15]=='\t43':
        data.iloc[i,15]='43'
    if data.iloc[i,16]=='\t?':
        data.iloc[i,16]=np.nan
    if data.iloc[i,16]=='\t6200':
        data.iloc[i,16]= '6200'
    if data.iloc[i,16]=='\t8400':
        data.iloc[i,16]= '6200'
    if data.iloc[i,17]=='\t?':
        data.iloc[i,17]=np.nan
    if data.iloc[i,24]=='ckd':
        data.iloc[i,24]='yes'
    if data.iloc[i,24]=='notckd':
        data.iloc[i,24]='no'

#One-hot encoding some categorical features, some categorical features must not be encoded since they are ordinal
data.replace({ 'normal' : 1, 'abnormal' : 0}, inplace = True)
data.replace({ 'present' : 1, 'notpresent' : 0}, inplace = True)
data.replace({ 'yes' : 1, '\tyes':1, ' yes':1, '\tno':0, 'no' : 0}, inplace = True)
data.replace({ 'good' : 1, 'poor' : 0}, inplace = True)
data.replace({ 'ckd' : 1, 'ckd\t':1, 'notckd' : 0}, inplace = True)

#Replacing missing values with NaN
data.replace('\t?',np.nan, inplace = True)        
data.replace('?',np.nan, inplace = True)

data.head()

"""Let's deal with mistyped features now."""

data.dtypes

"""Some numerical features are mistyped as strings.  

"""

for col in data.columns:
        data[col]=data[col].astype('float')

data.info()

"""Now that we've dealt with that, let's separate categorical and numerical features, as they won't be dealt with the same way.  """

#Creating two lists of numerical and categorical features
numeric = ['Age (yrs)','Specific Gravity','Albumin','Sugar', 'Blood Pressure (mm/Hg)', 'Blood Glucose Random (mgs/dL)', 'Blood Urea (mgs/dL)', 'Serum Creatinine (mgs/dL)', 'Sodium (mEq/L)', 'Potassium (mEq/L)', 'Hemoglobin (gms)', 'Packed Cell Volume', 'White Blood Cells (cells/cmm)', 'Red Blood Cells (millions/cmm)']
categoricals=[]
for col in data.columns:
    if not col in numeric:
        categoricals.append(col)
categoricals.remove('Chronic Kidney Disease')

"""###### Note:
Note that Specific Gravity, Albumin and Sugar basically are categorical features. But because they're ordinal, they will be preprocessed as numerical.
"""

numeric

categoricals

"""Now that the data is cleaned, we need to deal with those missing values.  
We'll do some further exploration first, as that could help us in picking a proper imputation method.

### Further Exploration

We'll start by visualizing feature distributions.
"""

import matplotlib.style as style
style.use('fivethirtyeight')

n_rows, n_cols = (int(len(numeric)/2),2) #Since we have 14 numerical features in total
#Initializing the subplot
figure, axes = plt.subplots(nrows=n_rows, ncols=n_cols,figsize=(20, 50))
figure.suptitle('\n\nDistributions of Numerical Features')

for index, column in enumerate(numeric):
    
    #The "coordinates" of each plot
    i,j = (index // n_cols), (index % n_cols)
    
    #Calculating the missing values percentage
    miss_perc="%.2f"%(100*(1-(data[column].dropna().shape[0])/data.shape[0]))
    
    collabel=column+"\n({}% is missing)".format(miss_perc)
    
    #Visualising the distribution of the numerical features
    fig=sns.distplot(data[column], color="g", label=collabel, norm_hist=True,
    
    ax=axes[i,j], kde_kws={"lw":4})
    
    fig=fig.legend(loc='best')
    
    axes[i,j].set_ylabel("Probability Density")
    
    axes[i,j].set_xlabel(None)

plt.show()

"""##### Notes:
Some features show some very distant outliers.  
Some others have discrete values, but we will be treating them like continuous ones.  
The reason being is that these are measures of biological variables which are in reality continuous.   
Them being discrete is probably due to the method they've been measured with.  
Some features have high proportions of missing values, thus they cannot be imputed with measures of central tendency. That would distort their distributions.  
Plus, some features are very skewed while others are almost normal, some have a very distinct mode while some don't. Which means even if we didn't have so many missing values, we'd have to deal with each feature separately.

Let's take a look at categorical features now.
"""

style.use('seaborn-darkgrid')

n_rows, n_cols = (int(len(categoricals)/2),2) #Since we have 10 categorical features in total

#Initializing the subplot
figure, axes = plt.subplots(nrows=n_rows, ncols=n_cols,figsize=(30, 50))
figure.suptitle('\n\nCountplots of Categorical Features')

for index, column in enumerate(categoricals):
    
    #The "coordinates" of each plot
    i,j = index // n_cols, index % n_cols
    
    #Calculating the missing values percentage
    miss_perc="%.2f"%(100*(1-(data[column].dropna().shape[0])/data.shape[0]))
    
    collabel=column+"\n({}% is missing)".format(miss_perc)
    
    #Visualising the count of the categorical features
    fig = sns.countplot(x=column, data=data,label=collabel, palette=sns.cubehelix_palette(rot=-.35,light=0.85,hue=1),
    
    ax=axes[i,j])
    
    axes[i,j].set_title(collabel)
    
    axes[i,j].set_xlabel(None)
    
    axes[i,j].set_ylabel("Count")
    
    axes[i,j].set_xticklabels(axes[i,j].get_xticklabels())

plt.show()

"""##### Notes:
Some features have very high percentages of missing values while some have almost none.  
Certain abnormalities/diseases seem relatively commun in this dataset, such as diabetes and hypertension.  
this sample of 400 people may not well-represent the population of India (which is where the data was collected), nor any other population.  

"""

#Calculating the missing values percentage of the target
miss_perc="%.2f"%(100*(1-(data['Chronic Kidney Disease'].dropna().shape[0])/data.shape[0]))
    
label="Disease\n(missing:\n{}%)".format(miss_perc)

#Visualising the count of the target
fig=sns.countplot(x=data['Chronic Kidney Disease'],label=label, palette=sns.cubehelix_palette(rot=-.35,light=0.85,hue=1))
plt.title("Disease\n({}% is missing)".format(miss_perc))
plt.show()

"""##### Notes:
We can see there are 0 missing values in the target, which is logical because this is not a semi-supervised problem.

This further shows that this dataset represents neither a country/community nor even a group of ill people (more than 60% of the population is ill).

Let's take a look at missing values.
"""

style.use('seaborn-darkgrid')

d=((data.isnull().sum()/data.shape[0])).sort_values(ascending=False)
d.plot(kind='bar',
       color=sns.cubehelix_palette(start=2,
                                    rot=0.15,
                                    dark=0.15,
                                    light=0.95,
                                    reverse=True,
                                    n_colors=24),
        figsize=(20,10))
plt.title("\nProportions of Missing Values:\n")
plt.show()

"""### Data Transformations"""
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import QuantileTransformer
from sklearn.preprocessing import PowerTransformer
from sklearn.preprocessing import StandardScaler
from sklearn.preprocessing import RobustScaler
from sklearn.preprocessing import MinMaxScaler

"""The Quantile Transformer transforms a distribution into a normal or uniform one. We will be trying both.  
The Power Transformer applies another non-linear transformation to make your data more normal-like.  
StandardScaler standardizes your features.  
RobustScaler centers data but, instead of dividing by the standard deviation, it divides by an inter-quantile range that can be specified (to minimize the effect of the outliers).  
You can either specify the inter-quantile range or just leave it to default, which is [25,75].
"""

NQT=QuantileTransformer(output_distribution='normal')
UQT=QuantileTransformer(output_distribution='uniform')
SPT=PowerTransformer()
RS=RobustScaler() #default
WRS=RobustScaler(quantile_range=(15,85)) # a "wider" range
SS=StandardScaler()

Transformers=[NQT,UQT,SPT,RS,WRS,SS]
tr_names = ['Normal Quantile Transformer', 'Uniform Quantile Transformer', 'Power Transformer', 'Robust Scaler', 'Wide Robust Scaler', 'Standard Scaler']

#Seperating the dataset into numerical and categorical datasets
categorical_feats = pd.DataFrame()
numeric_feats = pd.DataFrame()
for col in categoricals:
  categorical_feats=pd.concat([categorical_feats, data[col]], axis = 1)
for col in numeric:
  numeric_feats=pd.concat([numeric_feats, data[col]], axis = 1)

#Ordering the variables by their type (numerical/categorical)
data = pd.concat([numeric_feats, categorical_feats, data['Chronic Kidney Disease']], axis = 1)

#Applying each transformer to the numerical features and storing all the outcomes in a list of arrays
datarrays=[]
for tr in Transformers:
    arr=tr.fit_transform(numeric_feats)
    datarrays.append(arr)

#Creating a DataFrame for each outcome and storing them in a list
dataframes=[numeric_feats]
for arr in datarrays:
    df=pd.DataFrame(arr,columns=numeric_feats.columns)
    df = pd.concat([df, categorical_feats, data['Chronic Kidney Disease']], axis = 1)
    dataframes.append(df)

"""Let's take a look at what these transformations did to our data.  
P.S: the second (blue) robustscaler is the wider one, and the first (orange) powertransformer is the normalized one.
"""

style.use('fivethirtyeight')

colors=['crimson','steelblue','darkorange','darkviolet','gold','mediumblue','lime']

n_rows, n_cols = (len(numeric),7) #Since we have 14 numerical features and 6 transformers(+the untransformed dataset)

#Initializing the subplots
figure, axes = plt.subplots(nrows=n_rows, ncols=n_cols,figsize=(70, 100))
figure.suptitle('\n\nDistributions of Numerical Features\nAfter Different Transformations')

for i, col in enumerate(numeric):
    #Visualizing the distribution of each numercial feature
    fig = sns.distplot(data[col], color="g", label='Original\nDistribution', norm_hist=True,
    
    ax=axes[i,0], kde_kws={"lw":4})
    
    fig=fig.legend(loc='best')
    
    axes[i,0].set_xlabel(axes[i,0].get_xlabel())
    
    axes[i,0].set_ylabel("Probability Density")

for j in range(1,7):
    for i, col in enumerate(numeric):
        #Assigning a label to each graph
        label=tr_names[j-1]
        
        #Visualizing the distribution of each numerical feature after each transformation
        fig = sns.distplot(dataframes[j][col], color=colors[j-1], label=label, norm_hist=True,

        ax=axes[i,j], kde_kws={"lw":4})
        
        fig=fig.legend(loc='best')
    
        axes[i,j].set_ylabel("Probability Density")
        
        axes[i,j].set_xlabel(axes[i,j].get_xlabel())

plt.show()

"""##### Notes:
Both quantile transformers did a very decent job (despite the piles of outliers mentionned earlier)  
The unstandardized, normalized powertransformer (orange) performed quite awfully.  
The Standardized power transformer (purple) is, in contrast, quite decent.  
Linear transformers have almost identical results.  Good ones nonetheless.
Non-linear transformations (from red to purple) don't seem to have dealt with ordinal features well.  
But we only get to judge after seeing the imputation results.  
The gaussian quantile transformer (red) piled up outliers on the edges.
Linear transformers (last three) didn't change shapes of distributions.  
Everything will be evaluated after imputation.

### Imputation
"""

from sklearn.impute import KNNImputer

knnimp=KNNImputer(weights='distance', n_neighbors=8)

#Imputing the original dataset
data_imp = knnimp.fit_transform(data)

#Imputing the transformed datasets
rrr=[data.to_numpy()]
for dfi in range(1,len(dataframes)):
    rrr.append(knnimp.fit_transform(dataframes[dfi]))

impdf=[]
for i in range(len(rrr)):
    impdf.append(pd.DataFrame(rrr[i],columns=data.columns))

n_rows, n_cols = (len(numeric),7)

figure, axes = plt.subplots(nrows=n_rows, ncols=n_cols,figsize=(70, 100))
figure.suptitle('\n\nDistributions of Numerical Features\nAfter Imputation')
for i,col in enumerate(numeric):
    fig = sns.distplot(data[col], color="g", label='Original Feature\n Distribution', norm_hist=True,
    
    ax=axes[i,0], kde_kws={"lw":4})
    
    fig=fig.legend(loc='best')
    
    axes[i,0].set_xlabel(axes[i,0].get_xlabel())
    
    axes[i,0].set_ylabel("Probability Density")

for j in range(1,7):
    for i, col in enumerate(numeric):
        label=tr_names[j-1]
        
        fig = sns.distplot(impdf[j][col], color=colors[j-1], label=label, norm_hist=True,

        ax=axes[i,j], kde_kws={"lw":4})
        
        fig=fig.legend(loc='best')
    
        axes[i,j].set_ylabel("Probability Density")
        
        axes[i,j].set_xlabel(axes[i,j].get_xlabel())

plt.show()

"""Finally, we can conclude that the transformer that best kept the distribution of the data is the wide robust scaler, which is pretty logical since we have a few bust serious outliers

# Exploratory Data Analysis
"""

style.use('seaborn-darkgrid')

n_rows, n_cols = (10,2)

figure, axes = plt.subplots(nrows=n_rows, ncols=n_cols,figsize=(25, 130))
figure.suptitle('\n\n\nDistributions of Categorical Variables\n(Original Data)')

for i in range(len(categoricals)):
    column=categoricals[i]
    graph1=data[column].value_counts().plot.pie(autopct='%1.1f%%',
                                                      ax=axes[i,0],
                                                      colormap="tab20c",
                                                      shadow=True,
                                                      explode=[0.1,0])
    axes[i,0].set_ylabel('%')
    axes[i,0].set_title(column+' (percentages)')
    graph2=sns.countplot(x=column,
                         data=data,
                         palette='Blues_r',
                         ax=axes[i,1])
    axes[i,1].set_xlabel(None)
    axes[i,1].set_ylabel('Count')
    axes[i,1].set_xticklabels(axes[i,1].get_xticklabels())
    axes[i,1].set_title(column+' (value counts)')
    

graph1=data['Chronic Kidney Disease'].value_counts().plot.pie(autopct='%1.1f%%',
                                                              ax=axes[9,0],
                                                              colormap='tab20c',
                                                              shadow=True,
                                                              explode=[0.1,0])
axes[9,0].set_ylabel("%")
axes[9,0].set_title('Chronic Kidney Disease (percentages)')


graph2=sns.countplot(x='Chronic Kidney Disease',
                     data=data,
                     palette='Blues_r',
                     ax=axes[9,1])
axes[9,1].set_xlabel(None)
axes[9,1].set_ylabel("Count")
axes[9,1].set_xticklabels(axes[9,1].get_xticklabels())
axes[9,1].set_title('Chronic Kidney Disease (value counts)')

plt.show()

n_rows, n_cols = (10,10)

figure, axes = plt.subplots(nrows=n_rows, ncols=n_cols,figsize=(70, 100))
figure.suptitle('\n\nCrosstabs of Categorical Variables (Original Data)\n')

for i in range(10):
    for j in range(10):
        sns.heatmap(
                    pd.crosstab(data[categoricals[i]],data[categoricals[j]]),
                    ax=axes[i,j],
                    cmap=sns.cubehelix_palette(start=2.8, rot=.1),
                    square='True',
                    cbar=False,
                    annot=True,
                    fmt='d')
        
        axes[i,j].set_xlabel(axes[i,j].get_xlabel())
        
        axes[i,j].set_ylabel(axes[i,j].get_ylabel())
        
plt.show()

style.use('seaborn-darkgrid')

n_rows, n_cols = (14,2)

figure, axes = plt.subplots(nrows=n_rows, ncols=n_cols,figsize=(25, 100))
figure.suptitle('\n\n\nDistributions of Numerical Variables\n(Original Data)')

for i in range(len(numeric)):
    col=numeric[i]
    
    label='Mean = {}\nMedian = {}\nStandard Deviation = {}'.format(str("%.2f"%data[col].mean()),
                                                                    str("%.2f"%data[col].median()),
                                                                    str("%.2f"%data[col].std()))
    
    graph1=sns.distplot(data[col],
                        color="navy",
                        ax=axes[i,0],
                        kde_kws={"lw":4},
                        norm_hist=True,
                        label=label).legend(loc='best')
    axes[i,0].set_title(col+': Density')
    axes[i,0].set_xlabel(None)
    axes[i,0].set_ylabel("Pobability Density")

    graph20=sns.violinplot(x=col,
                          data=data,
                          ax=axes[i,1],
                          color='lavender',
                          inner='box')
    graph21=sns.boxplot(x=col,
                        data=data,
                        ax=axes[i,1],
                        fliersize=8,
                        boxprops=dict(alpha=0))
    
    axes[i,1].set_xlabel(None)
    axes[i,1].set_title(col+': Quartiles')
    
    
plt.show()

numericdat=data.drop(categoricals, axis=1, inplace=False)

plt.figure(figsize=(20,20))

sns.heatmap(numericdat.corr("pearson"),
            cmap=sns.diverging_palette(280, 280, s=100, l=35, as_cmap=True,sep=80),
            square=True,
            annot=True,
            fmt='.2%',
            cbar=False)
plt.title("Pearson Correlation Matrix\n")
plt.show()

"""##### Notes:
We can notice high correlations(>70% and >-70%) between certain columns.  
"""

n_rows, n_cols = (5,2)

figure, axes = plt.subplots(nrows=n_rows, ncols=n_cols,figsize=(30, 100))
figure.suptitle('\n\nCategorical Features\nVS\nTarget Variable')

for index, column in enumerate(categoricals):
    
    i,j = (index // n_cols), (index % n_cols)
    
    sns.heatmap(pd.crosstab(data[column],data['Chronic Kidney Disease']),
                ax=axes[i,j],
                cmap=sns.cubehelix_palette(start=2.8, rot=.1),
                square='True',
                cbar=False,
                annot=True,
                fmt='d')
        
    axes[i,j].set_xlabel("Disease")

    axes[i,j].set_ylabel(column)
    
    axes[i,j].set_yticklabels(axes[i,j].get_yticklabels())
    
    axes[i,j].set_xticklabels(["No CKD","CKD"])

plt.show()

n_rows, n_cols = (7,2)

figure, axes = plt.subplots(nrows=n_rows, ncols=n_cols,figsize=(20, 60))
figure.suptitle('\n\nNumerical Features\nVS\nTarget Variable')

for index, column in enumerate(numeric):
    
    i,j = (index // n_cols), (index % n_cols)
    
    bp=sns.boxplot(y=column, x='Chronic Kidney Disease', data=data, color="paleturquoise",
    
    ax=axes[i,j])
        
    axes[i,j].set_xlabel(axes[i,j].get_xlabel())

    axes[i,j].set_ylabel(column)
    
    axes[i,j].set_xticklabels(axes[i,j].get_xticklabels())

plt.show()

colors3=['deepskyblue','turquoise','mediumspringgreen','turquoise']

n_rows, n_cols = (14,10)

figure, axes = plt.subplots(nrows=n_rows, ncols=n_cols,figsize=(60, 60))
figure.suptitle('\nNumerical and Categorical Features:\nDistributions and Correlations')

for i in range(14):
    for j in range(10):
        graph=sns.violinplot(y=numeric[i],x=categoricals[j],data=data,color=colors3[j%4],ax=axes[i,j])
plt.show()

""" Prediction"""

X=data_imp[:,:24]
Y=data_imp[:,24]

full_scaled_data=SS.fit_transform(data)
scaled_data=WRS.fit_transform(X)

from sklearn.model_selection import train_test_split
X_train, X_test, Y_train, Y_test = train_test_split(scaled_data, Y, test_size=0.2, random_state=12)

"""### Linear-Kernel SVC

The distributions shown in the next graph represent LDA results only on training data
"""

from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from sklearn.svm import SVC
from sklearn.metrics import accuracy_score
from sklearn.decomposition import PCA

lin_svc=SVC(kernel='linear')

n_rows, n_cols= 12,2

figure, axes = plt.subplots(nrows=n_rows,ncols= n_cols, figsize=(30, 120))

figure.suptitle('\nLDA with Linear SVC\n(Distributions represent\nonly the training data)')

for index in range(24):
    
    i,j = (index // n_cols), (index % n_cols)
    
    pca=PCA(n_components=index+1)
    
    lda=LinearDiscriminantAnalysis()
    
    some_pipe=make_pipeline(pca,lda)
    
    X_lda_train=some_pipe.fit_transform(X_train,Y_train)
    
    X_lda_test=some_pipe.fit_transform(X_test,Y_test)
    
    lin_svc.fit(X_lda_train,Y_train)
    
    y_pred_train=lin_svc.predict(X_lda_train)
    
    train_acc= accuracy_score(y_pred_train,Y_train)
    
    y_pred_test=lin_svc.predict(X_lda_test)
    
    test_acc= accuracy_score(y_pred_test,Y_test)
    
    X_lda_train=X_lda_train.reshape((320,))
    
    bp=sns.boxenplot(y=X_lda_train, x=Y_train, color="paleturquoise",showfliers=True,ax=axes[i,j])
    
    axes[i,j].set_title("n° Of PCA Components: {}\nTraining Accuracy: {}\nTesting Accuracy: {}".format(index+1,
                                                                                                       "%.3f"%train_acc,
                                                                                                       "%.3f"%test_acc))
    axes[i,j].set_xlabel(None)
    
    axes[i,j].set_xticklabels(["CKD","No CKD"])
    
plt.show()

"""Low variance despite the fact that the testing set is 0.2 of the whole dataset, which only has 400 samples.

### Evaluating A Few Other Models
"""

from sklearn.neighbors import KNeighborsClassifier
from sklearn.naive_bayes import GaussianNB
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier

SVM_RBF=SVC()
    
SVM_Poly2=SVC(kernel='poly',degree=2)
    
SVM_Poly3=SVC(kernel='poly',degree=3)

KNN3=KNeighborsClassifier(n_neighbors=3,weights='distance')

KNN8=KNeighborsClassifier(n_neighbors=8,weights='distance')

KNN15=KNeighborsClassifier(n_neighbors=15,weights='distance')

Naive_Bayes=GaussianNB()

LogReg=LogisticRegression()

Tree=DecisionTreeClassifier()

Forest=RandomForestClassifier()

models=[SVM_RBF,SVM_Poly2,SVM_Poly3,KNN3,KNN8,KNN15,Naive_Bayes,LogReg,Tree,Forest]

names=["SVM_RBF","SVM_Poly2","SVM_Poly3","Weighted 3NearestNeighbors","Weighted 8NearestNeighbors",
       "Weighted 15NearestNeighbors","Naive Bayes","Logistic Regression","Decision Tree","Random Forest"]

n_rows, n_cols= 10,1

figure, axes = plt.subplots(nrows=n_rows,ncols= n_cols, figsize=(30, 120))

figure.suptitle('\nEvaluating Different Models')



tr_mask = np.empty(shape=(24,1),dtype="object")
    
ts_mask = np.empty(shape=(24,1),dtype="object")

for i in range(24):
    tr_mask[i]="Training"
    ts_mask[i]="Testing"

mask = np.vstack((tr_mask,ts_mask))

mask=mask.reshape((48,))

cmps=[i for i in range(1,25)] * 2


for index in range(10):
    
    pca_tr_acc=[]
    
    pca_ts_acc=[]
    
    
    for n_comps in range(1,25):
        
        model=models[index]
        
        pca=PCA(n_components=n_comps)
        
        pca_model=make_pipeline(pca,model)
        
        pca_model.fit(X_train,Y_train)
        
        y_tr_pred= pca_model.predict(X_train)
        
        pca_tr_acc.append(accuracy_score(y_tr_pred,Y_train))
        
        y_ts_pred=pca_model.predict(X_test)
        
        pca_ts_acc.append(accuracy_score(y_ts_pred,Y_test))
        
    
    model_data = pd.DataFrame()
    
    model_data["PCA"] = pca_tr_acc + pca_ts_acc
        
    model_data["Results"] = mask
    
    sns.barplot(x=cmps, y="PCA", hue="Results", data=model_data, palette='cool', ax=axes[index]).set(ylim=(0.8,1))
    
    axes[index].set_title(names[index])
    
    axes[index].set_xlabel("n° of PCA Components")
    axes[index].set_ylabel("Accuracy")
    
    axes[index].set_xticklabels(axes[index].get_xticklabels())
    
    
plt.show()

from sklearn.ensemble import AdaBoostClassifier

boost_models = [SVC(),
 SVC(degree=2, kernel='poly'),
 SVC(kernel='poly'),
 GaussianNB(),
 LogisticRegression(),
 DecisionTreeClassifier(),
 RandomForestClassifier()]

for mod in boost_models:
  booster = AdaBoostClassifier(base_estimator = mod, algorithm = 'SAMME')
  booster.fit(X_train, Y_train)
  print(mod, booster.score(X_test, Y_test))

"""As we can see the models didn't really improve comparing to the ones without boosting

### Neural Networks

So We will be trying a small neural network with one hidden layer containing 4 neurons, and a bigger one with 3 hidden layers and lots of neurons.
"""

import tensorflow
from tensorflow.keras.layers import Dense
from tensorflow.keras.models import Sequential
from tensorflow.keras.callbacks import EarlyStopping
from tensorflow.keras.utils import to_categorical

early_stopping_monitor = EarlyStopping(patience=5, monitor='accuracy')
Y_net = to_categorical(Y)

pca_tr_acc_1=[]
    
pca_ts_acc_1=[]


pca_tr_acc_2=[]
    
pca_ts_acc_2=[]


for i in range(1,25):
    
    pca=PCA(n_components=i)
    
    X_pca=pca.fit_transform(scaled_data)
    
    X_pca_train, X_pca_test, Y_train, Y_test = train_test_split(X_pca, Y_net, test_size=0.25, random_state=12)
    
    #little net
    net1= Sequential()
    
    net1.add(Dense(4, activation='relu', input_shape = (i,)))
    
    net1.add(Dense(2, activation='softmax'))
    
    net1.compile(optimizer='adam',loss='binary_crossentropy',metrics=['accuracy'])
    
    net1.fit(X_pca_train, Y_train, epochs=50, callbacks=[early_stopping_monitor], verbose=0)
    
    y_tr_pred=net1.predict(X_pca_train)
    
    pca_tr_acc_1.append(accuracy_score(np.argmax(y_tr_pred, axis=1),Y_train[:,1]))
    
    y_ts_pred=net1.predict(X_pca_test)
    
    pca_ts_acc_1.append(accuracy_score(np.argmax(y_ts_pred, axis=1),Y_test[:,1]))
    
    
    
    #big net
    net2= Sequential()
    
    net2.add(Dense(50, activation='relu', input_shape = (i,)))
    
    net2.add(Dense(30, activation='relu'))
    
    net2.add(Dense(20, activation='relu'))
    
    net2.add(Dense(10, activation='relu'))
    
    net2.add(Dense(2, activation='softmax'))
    
    net2.compile(optimizer='adam',loss='binary_crossentropy',metrics=['accuracy'])
    
    net2.fit(X_pca_train, Y_train, epochs=100, callbacks=[early_stopping_monitor], verbose=0)
    
    y_tr_pred=net2.predict(X_pca_train)
    
    pca_tr_acc_2.append(accuracy_score(np.argmax(y_tr_pred, axis=1),Y_train[:,1]))
    
    y_ts_pred=net2.predict(X_pca_test)
    
    pca_ts_acc_2.append(accuracy_score(np.argmax(y_ts_pred, axis=1),Y_test[:,1]))

tr_mask = np.empty(shape=(24,1),dtype="object")
    
ts_mask = np.empty(shape=(24,1),dtype="object")

for i in range(24):
    tr_mask[i]="Training"
    ts_mask[i]="Testing"

mask = np.vstack((tr_mask,ts_mask))

mask=mask.reshape((48,))

cmps=[i for i in range(1,25)] * 2


net1_data = pd.DataFrame()
    
net1_data["PCA"] = pca_tr_acc_1 + pca_ts_acc_1

net1_data["Results"] = mask


net2_data = pd.DataFrame()
    
net2_data["PCA"] = pca_tr_acc_2 + pca_ts_acc_2

net2_data["Results"] = mask

n_rows, n_cols= 1,2

figure, axes = plt.subplots(nrows=n_rows,ncols= n_cols, figsize=(30, 10))

figure.suptitle('Little NN vs Big(ger) NN')



graph1=sns.barplot(x=cmps, y="PCA", hue="Results", data=net1_data, palette='cool', ax=axes[0]).set(ylim=(0.5,1))

axes[0].set_title("Little Neural Network")

axes[0].set_xlabel("n° of PCA Components")

axes[0].set_ylabel("Accuracy")

axes[0].set_xticklabels(axes[0].get_xticklabels())



graph2=sns.barplot(x=cmps, y="PCA", hue="Results", data=net2_data, palette='cool', ax=axes[1]).set(ylim=(0.5,1))

axes[1].set_title("Big(ger) Neural Network")

axes[1].set_xlabel("n° of PCA Components")

axes[1].set_ylabel("Accuracy")

axes[1].set_xticklabels(axes[1].get_xticklabels())

plt.show()
