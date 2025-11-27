Sub CreateCircle()
    ' Creates a circle at the origin with radius 50mm
    Dim swApp As SldWorks.SldWorks
    Dim swModel As SldWorks.ModelDoc2

    Set swApp = CreateObject("SldWorks.Application")
    Set swModel = swApp.ActiveDoc

    ' Insert sketch
    swModel.InsertSketch2 True

    ' Create circle at origin with radius 50mm (0.05m)
    swModel.CreateCircle2 0, 0, 0, 0.05

    ' Exit sketch
    swModel.InsertSketch2 False
End Sub
