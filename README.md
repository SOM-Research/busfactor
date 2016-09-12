# Bus Factor Analyzer

The tool is the result of the ongoing work published in the 22nd IEEE International Conference on Software Analysis, Evolution, and Reengineering (available for download at http://tinyurl.com/AssessingBusFactorForGitRepo). We would be very interested in getting feedback and helping people use it.

###How To

In order to run the tool you need to perform some steps:

1) Install Gitana (https://github.com/SOM-Research/Gitana/tree/0.2) 

2) Launch the Gitana GUI (gitana_gui.py) and extract your Git repository to a relational database

3) Export the obtained relational database to JSON (always through the Gitana GUI)

4) Launch the Bus Factor Analyzer GUI (https://github.com/valeriocos/BusFactor/blob/master/bus_factor_gui.py)

5) Select the path of the JSON file where the relational database has been exported

6) When the export has finished, execute tool.py (https://github.com/valeriocos/BusFactor/blob/master/tool.py) to visualize the result


###Settings

The Bus Factor Analyzer GUI allows you to tune the process to assess the bus factor for your Git repository. 
In particular you will be able to play with:

- **Primary developer knowledge.** 
Primary developers are those developers that have modified a minimum percentage X of a software artifact (e.g., file, 
directory, branch, file extension) of the repository. By default, X is set to 1/D, where D is the overall number of developers that have ever
modified the artifact. However, X can be changed to be, for instance, 1/2 (50% of the modifications over the artifact), 1/4 (25%) and so on.

- **Secondary developer knowledge.**
Secondary developers are those developers that know at least a proportion Y of what the primary developers know (X). By default,
Y is set to half of X (0.5), however it can be changed to a value between 0 and 1. In case you don't want to use 
the secondary developer knowledge parameter, you can set Y to 1.

- **Detail level.**
This parameter allows you to set the the granularity of the analysis, that can be based on developer modifications at file or line level.

- **Metric.**
This parameter is used to combine the importance of the number and order of modifications to assign the knowledge value. 
Note that depending on the level of detail selected, the four metrics are initially calculated at file or line level (just for text files).
Once the selected metric has been calculated, its calculation is repeated at each level of the repository to assign a bus factor value
to each directory, branch, file extension and the repository itself.

 - **Last change.** This metric assigns all knowledge of a line/file to the last developer that modified that
line (or file for binary files).

 - **Multiple changes.** This metric counts the number of times a line/file has been modified during the life-cycle of the project. 
 It assigns more knowledge to the developers that modified the line/file most times.

 - **Distinct changes**. This metric assesses the developer knowledge according to the number of non-consecutive changes on the line/file.
 
 - **Weighted distinct changes.** This metric assesses the developer knowledge by relying of the previous metric modified to take into account the position of the
modifications in the time-line evolution of the line/file. It is used to assign an incremental importance to the later modifications
on the line/file.

###Demo

A demo of the tool is available at https://github.com/atlanmod/busfactor_demo
