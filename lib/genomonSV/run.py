#!/usr/bin/env python


import sys, argparse, subprocess
import config 
import utils
import parseFunction
import filterFunction
import annotationFunction

def genomonSV_parse(args):

    """
        Genomon SV: parsing breakpoint containing read pairs and improperly aligned read pairs
    """

    ####################
    # load config files
    global sampleConf
    sampleConf = config.sample_yaml_config_parse(args.sampleInfoFile)

    global paramConf
    paramConf = config.param_yaml_contig_parse(args.paramInfoFile)
    ####################


    ####################
    # make output directories
    utils.make_directory(sampleConf["target"]["outputDir"])
    ####################

    
    ####################
    outputPrefix = sampleConf["target"]["outputDir"] + "/" + sampleConf["target"]["label"]

    # parse breakpoint containing read pairs from input bam files
    parseFunction.parseJunctionFromBam(sampleConf["target"]["path_to_bam"], 
                                       outputPrefix + ".junction.unsort.txt", 
                                       paramConf["parseJunctionCondition"])

    utils.sortBedpe(outputPrefix + ".junction.unsort.txt",
                    outputPrefix + ".junction.sort.txt")

    parseFunction.getPairStartPos(outputPrefix + ".junction.sort.txt",
                                  outputPrefix + ".junction.pairStart.bed")

    utils.compress_index_bed(outputPrefix + ".junction.pairStart.bed",
                             outputPrefix + ".junction.pairStart.bed.gz",
                             paramConf["software"]["bgzip"], paramConf["software"]["tabix"])



    parseFunction.getPairCoverRegionFromBam(sampleConf["target"]["path_to_bam"], 
                                            outputPrefix + ".junction.pairCoverage.txt",
                                            outputPrefix + ".junction.pairStart.bed.gz")


    parseFunction.addPairCoverRegionFromBam(outputPrefix + ".junction.sort.txt",
                                            outputPrefix + ".junction.sort.withPair.txt",
                                            outputPrefix + ".junction.pairCoverage.txt")

    parseFunction.clusterJunction(outputPrefix + ".junction.sort.withPair.txt", 
                                  outputPrefix + ".junction.clustered.bedpe.unsort",
                                  paramConf["clusterJunctionCondition"])

    utils.sortBedpe(outputPrefix + ".junction.clustered.bedpe.unsort", outputPrefix + ".junction.clustered.bedpe")

    utils.compress_index_bed(outputPrefix + ".junction.clustered.bedpe",
                             outputPrefix + ".junction.clustered.bedpe.gz",
                             paramConf["software"]["bgzip"], paramConf["software"]["tabix"])

    if paramConf["debugMode"] == False:
        subprocess.call(["rm", outputPrefix + ".junction.unsort.txt"])
        subprocess.call(["rm", outputPrefix + ".junction.sort.txt"])
        subprocess.call(["rm", outputPrefix + ".junction.pairStart.bed.gz"])
        subprocess.call(["rm", outputPrefix + ".junction.pairStart.bed.gz.tbi"])
        subprocess.call(["rm", outputPrefix + ".junction.sort.withPair.txt"])
        subprocess.call(["rm", outputPrefix + ".junction.pairCoverage.txt"])
        subprocess.call(["rm", outputPrefix + ".junction.clustered.bedpe.unsort"])
    ####################
    # improper read pairs

    # parse potentially improper read pairs from input bam files
    parseFunction.parseImproperFromBam(sampleConf["target"]["path_to_bam"],
                         outputPrefix + ".improper.unsort.txt",
                         paramConf["parseImproperCondition"])

    # create and organize bedpe file integrating pair information 
    parseFunction.makeImproperBedpe(outputPrefix + ".improper.unsort.txt",
                                    outputPrefix + ".improper.bedpe",
                                    paramConf["clusterImproperCondition"])

    # cluster read pairs possibly representing the same junction
    parseFunction.clusterImproperBedpe(outputPrefix + ".improper.bedpe",
                                       outputPrefix + ".improper.clustered.unsort.bedpe",
                                       paramConf["clusterImproperCondition"])

    utils.sortBedpe(outputPrefix + ".improper.clustered.unsort.bedpe",
                    outputPrefix + ".improper.clustered.bedpe")

    utils.compress_index_bed(outputPrefix + ".improper.clustered.bedpe",
                             outputPrefix + ".improper.clustered.bedpe.gz",
                             paramConf["software"]["bgzip"], paramConf["software"]["tabix"])

    if paramConf["debugMode"] == False:
        subprocess.call(["rm", outputPrefix + ".improper.unsort.txt"])
        subprocess.call(["rm", outputPrefix + ".improper.bedpe"])
        subprocess.call(["rm", outputPrefix + ".improper.clustered.unsort.bedpe"])
    ####################


def genomonSV_filt(args):


    ####################
    # load config files
    global sampleConf
    sampleConf = config.sample_yaml_config_parse(args.sampleInfoFile)

    global paramConf
    paramConf = config.param_yaml_contig_parse(args.paramInfoFile)
    ####################


    ####################
    # file existence check

 
    ####################
    outputPrefix = sampleConf["target"]["outputDir"] + "/" + sampleConf["target"]["label"]

    filterFunction.filterJuncNumAndSize(outputPrefix + ".junction.clustered.bedpe.gz",
                                        outputPrefix + ".junction.clustered.filt1.bedpe",
                                        paramConf["filterCondition"])


    if sampleConf["nonMatchedControlPanel"]["use"] == True:
        filterFunction.filterNonMatchControl(outputPrefix + ".junction.clustered.filt1.bedpe",
                                             outputPrefix + ".junction.clustered.filt2.bedpe",
                                             sampleConf["nonMatchedControlPanel"]["data_path"],
                                             sampleConf["nonMatchedControlPanel"]["matchedControl_label"],
                                             paramConf["filterCondition"])
    else:
        subprocess.call(["cp", outputPrefix + ".junction.clustered.filt1.bedpe", outputPrefix + ".junction.clustered.filt2.bedpe"])

       
    filterFunction.addImproperInfo(outputPrefix + ".junction.clustered.filt2.bedpe",
                                   outputPrefix + ".junction.clustered.filt3.bedpe",
                                   outputPrefix + ".improper.clustered.bedpe.gz")

    filterFunction.filterMergedJunc(outputPrefix + ".junction.clustered.filt3.bedpe",
                                    outputPrefix + ".junction.clustered.filt4.bedpe",
                                    paramConf["filterCondition"])

    filterFunction.removeClose(outputPrefix + ".junction.clustered.filt4.bedpe",
                               outputPrefix + ".junction.clustered.filt5.bedpe",
                               paramConf["filterCondition"])

    filterFunction.validateByRealignment(outputPrefix + ".junction.clustered.filt5.bedpe",
                    outputPrefix + ".junction.clustered.filt6.bedpe",
                    sampleConf["target"]["path_to_bam"],
                    sampleConf["matchedControl"]["path_to_bam"],
                    paramConf["software"]["blat"] + " " + paramConf["software"]["blat_option"],
                    paramConf["realignmentValidationCondition"])

    filterFunction.filterNumAFFis(outputPrefix + ".junction.clustered.filt6.bedpe", 
                                  outputPrefix + ".junction.clustered.filt7.bedpe",
                                  paramConf["realignmentValidationCondition"])

    annotationFunction.addAnnotation(outputPrefix + ".junction.clustered.filt7.bedpe",
                                     outputPrefix + ".genomonSV.result.txt",
                                     paramConf["annotation"])

    if paramConf["debugMode"] == False:
        subprocess.call(["rm", outputPrefix + ".junction.clustered.filt1.bedpe"])
        subprocess.call(["rm", outputPrefix + ".junction.clustered.filt2.bedpe"])
        subprocess.call(["rm", outputPrefix + ".junction.clustered.filt3.bedpe"])
        subprocess.call(["rm", outputPrefix + ".junction.clustered.filt4.bedpe"])
        subprocess.call(["rm", outputPrefix + ".junction.clustered.filt5.bedpe"])
        subprocess.call(["rm", outputPrefix + ".junction.clustered.filt6.bedpe"])
        subprocess.call(["rm", outputPrefix + ".junction.clustered.filt7.bedpe"])

    ####################


