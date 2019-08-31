# SumoNetVis
A Python library for visualizing a Sumo network and trajectories with matplotlib.

![Example plot of an intersection](Example_Plot.png)

## Installation
Simply download this repository to your working directory. You can then import the library with the following line:

```python
import SumoNetVis
```

If you have problems with your IDE's autocomplete feature, use this instead:

```python
try:
    import .SumoNetVis
except Exception:
    import SumoNetVis
```

### Dependencies
* shapely
* matplotlib

## Usage
To plot a Sumo net file, you can use the following code:

```python
net = Net("path/to/yourfile.net.xml")
fig, ax = plt.subplots()
net.plot(ax)
# Insert code for overlay plots here
plt.show()
```

## Contribution
Issues and pull requests are welcome.
