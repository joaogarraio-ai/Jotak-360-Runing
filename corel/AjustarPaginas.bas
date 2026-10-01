Attribute VB_Name = "AjustarPaginas"
' Macro CorelDRAW - para cada página do documento:
'   1) desagrupa tudo
'   2) apaga o fundo branco (forma com preenchimento branco que cobre a página)
'   3) agrupa o que sobrou
'   4) aumenta um pouco
'   5) centraliza na página
' Ajuste AUMENTO abaixo (1.10 = +10%).

Private Const AUMENTO As Double = 1.1
Private Const COBERTURA_FUNDO As Double = 0.9 ' forma >= 90% da página é considerada fundo

Public Sub AjustarTodasAsPaginas()
    If ActiveDocument Is Nothing Then Exit Sub

    Dim pg As Page, sr As ShapeRange, s As Shape, g As Shape
    Dim i As Long, fator As Double, avisos As String

    ActiveDocument.BeginCommandGroup "Ajustar paginas"
    Application.Optimization = True

    For Each pg In ActiveDocument.Pages
        pg.Activate

        ' 1) desagrupar tudo
        Set sr = pg.Shapes.All
        If sr.Count = 0 Then GoTo proxima
        sr.UngroupAll

        ' 2) remover fundo branco
        Set sr = pg.Shapes.All
        For i = sr.Count To 1 Step -1
            Set s = sr(i)
            If EhFundoBranco(s, pg) Then s.Delete
        Next i

        ' 3) agrupar
        Set sr = pg.Shapes.All
        If sr.Count = 0 Then GoTo proxima
        Set g = sr.Group

        ' 4) aumentar (limitado para caber na página)
        fator = AUMENTO
        If g.SizeWidth * fator > pg.SizeWidth Then fator = pg.SizeWidth / g.SizeWidth
        If g.SizeHeight * fator > pg.SizeHeight Then
            If pg.SizeHeight / g.SizeHeight < fator Then fator = pg.SizeHeight / g.SizeHeight
        End If
        If fator < AUMENTO Then avisos = avisos & " " & pg.Index
        g.Stretch fator, fator

        ' 5) centralizar na página
        g.CenterX = pg.CenterX
        g.CenterY = pg.CenterY
proxima:
    Next pg

    Application.Optimization = False
    ActiveDocument.EndCommandGroup
    ActiveWindow.Refresh

    If Len(avisos) > 0 Then
        MsgBox "Concluído. Nas páginas:" & avisos & " o aumento foi limitado para caber na página.", vbInformation
    Else
        MsgBox "Concluído.", vbInformation
    End If
End Sub

Private Function EhFundoBranco(s As Shape, pg As Page) As Boolean
    EhFundoBranco = False
    If s.Fill.Type <> cdrUniformFill Then Exit Function
    With s.Fill.UniformColor
        If .Type <> cdrColorRGB Then s.Fill.UniformColor.ConvertToRGB
        If .RGBRed <> 255 Or .RGBGreen <> 255 Or .RGBBlue <> 255 Then Exit Function
    End With
    If s.SizeWidth >= pg.SizeWidth * COBERTURA_FUNDO And _
       s.SizeHeight >= pg.SizeHeight * COBERTURA_FUNDO Then EhFundoBranco = True
End Function
