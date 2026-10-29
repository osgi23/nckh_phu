"""Colors are shared by file index, console and HTML reports."""
from importlib import import_module
GROUPS={
"blue":{"label":"Cơ sở","color":"#2563eb","ansi":"\033[94m"},
"orange":{"label":"So sánh","color":"#c2410c","ansi":"\033[33m"},
"purple":{"label":"Mô hình chính","color":"#9333ea","ansi":"\033[95m"}}
METHODS={
"K-means":("blue","blue_baselines.kmeans",True),
"FCM":("blue","blue_baselines.fcm",True),
"PFCM":("blue","blue_baselines.pfcm",True),
"DP-FCM":("blue","blue_baselines.dp_fcm",True),
"DP-PFCM":("blue","blue_baselines.dp_pfcm",True),
"DP-GA-PFCM":("purple","purple_main_model.dp_ga_pfcm",True),
"DP-PSO-PFCM":("orange","orange_comparisons.dp_pso_pfcm",True),
"DP-SCA-PFCM":("orange","orange_comparisons.dp_sca_pfcm",True),
"DP-FBI-PFCM":("orange","orange_comparisons.dp_fbi_pfcm",True),
"GA-IFWCOM":("orange","orange_comparisons.ga_ifwcom",False),
"SCA-FPCOM":("orange","orange_comparisons.sca_fpcom",False)}
STAGES={
"baselines":["K-means","FCM","PFCM","DP-FCM","DP-PFCM"],
"comparisons":["DP-PFCM","DP-GA-PFCM","DP-PSO-PFCM","DP-SCA-PFCM","DP-FBI-PFCM","GA-IFWCOM","SCA-FPCOM"],
"main":["DP-GA-PFCM"],"all":list(METHODS)}
def fit_method(name,X,k,rng,cfg):
    return import_module(METHODS[name][1]).fit(X,k,rng,cfg)
