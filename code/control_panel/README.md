# Tutorials:

Layout:
* https://dash.plotly.com/layout
* https://towardsdatascience.com/dash101-part-1-introduction-to-dash-layout-810ec449ad43
* https://towardsdatascience.com/dash101-part-2-prettify-dash-dashboard-with-css-and-python-3866c069a3b6#9545-2086b581103

Style:
* https://dash.plotly.com/external-resources

Express: (Line charts, maps and more):
* https://plotly.com/python/line-charts/
* https://plotly.com/python/plotly-express/

Colors, and grouping:
* https://plotly.com/python/px-arguments/

https://dash.plotly.com/external-resources


Examples:
https://dash.gallery/Portal/
https://github.com/plotly/dash-sample-apps/blob/main/apps/dash-avs-explorer/app.py

# Issues
1. Copy yaml file to log folder, and display it with the app.py
2. District based simulation (losses.py and generate.py should be edited)
3. Add map to the visualizer
4. Add age, and country line plots:
    * The choosable sims change in time, based on the threshold
    * Ground truth
5. Remove hand-crafted variables from loss (day shifts etc.)
6. Add data repo in server /home/shaderd/KSH, and make a variable for the repo, which points to this folder
7. Set random seed for each C++ run (the set can be the ID)