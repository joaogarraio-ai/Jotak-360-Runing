Attribute VB_Name = "SubliTeste"
' =====================================================================
'  Jotak Sublimacao - Modelo de teste
'  Cria um documento novo já com moldes, artes e uma página de mockup
'  nomeados no padrão das macros, para testar tudo sem desenhar nada.
' =====================================================================
Option Explicit

Public Sub CriarModeloDeTeste()
    Dim doc As Document, pg As Page, lr As Layer
    Dim tams As Variant, larg As Variant, alt As Variant
    Dim i As Long, x As Double, s As Shape
    Dim frenteM As Shape, costasM As Shape

    Set doc = CreateDocument
    doc.Unit = cdrMillimeter
    doc.BeginCommandGroup "Modelo de teste"

    Set pg = doc.Pages(1)
    pg.Name = "ARTE"
    pg.SetSize 2600, 1900
    Set lr = pg.ActiveLayer

    ' Moldes graduados P, M, G, GG para frente e costas
    tams = Array("P", "M", "G", "GG")
    larg = Array(480, 520, 560, 600)
    alt = Array(680, 720, 760, 800)
    x = 50
    For i = 0 To 3
        Set s = CriarMolde(lr, "FRENTE", CStr(tams(i)), x, 1050, CDbl(larg(i)), CDbl(alt(i)))
        If tams(i) = "M" Then Set frenteM = s
        Set s = CriarMolde(lr, "COSTAS", CStr(tams(i)), x, 100, CDbl(larg(i)), CDbl(alt(i)))
        If tams(i) = "M" Then Set costasM = s
        x = x + larg(i) + 60
    Next i

    CriarArteFrente lr, frenteM
    CriarArteCostas lr, costasM

    CriarPaginaMockup doc

    pg.Activate
    doc.EndCommandGroup

    MsgBox "Modelo de teste criado." & vbCr & vbCr & _
           "Agora rode (Alt+F8), nesta página ARTE:" & vbCr & _
           "1. GerarMoldesPorTamanho" & vbCr & _
           "2. GerarNomesENumeros (use o exemplo_nomes.csv; os tamanhos BL-P não existem e vão gerar aviso)" & vbCr & _
           "3. GerarMockups" & vbCr & vbCr & _
           "Para o encaixe, selecione peças em qualquer página e rode EncaixarSelecao.", _
           vbInformation, "Jotak Sublimação"
End Sub

Private Function CriarMolde(lr As Layer, ByVal peca As String, ByVal tam As String, _
                            ByVal x As Double, ByVal y As Double, _
                            ByVal w As Double, ByVal h As Double) As Shape
    Dim s As Shape, t As Shape
    Set s = lr.CreateRectangle2(x, y, w, h)
    s.Fill.UniformColor.RGBAssign 255, 255, 255
    s.Outline.Width = 0.5
    s.Name = PREFIXO_MOLDE & peca & "_" & tam
    ' Etiqueta só para orientação (não faz parte do molde)
    Set t = lr.CreateArtisticText(x, y - 40, peca & " " & tam, , , "Arial", 48)
    t.Name = "ROTULO"
    Set CriarMolde = s
End Function

Private Sub CriarArteFrente(lr As Layer, molde As Shape)
    Dim sr As ShapeRange, fundo As Shape, circulo As Shape, txt As Shape, g As Shape
    Set sr = CreateShapeRange

    Set fundo = lr.CreateRectangle2(molde.CenterX - molde.SizeWidth / 2 - 10, _
                                    molde.CenterY - molde.SizeHeight / 2 - 10, _
                                    molde.SizeWidth + 20, molde.SizeHeight + 20)
    fundo.Fill.UniformColor.RGBAssign 0, 70, 160
    fundo.Outline.SetNoOutline
    sr.Add fundo

    Set circulo = lr.CreateEllipse2(molde.CenterX, molde.CenterY + 120, 110, 110)
    circulo.Fill.UniformColor.RGBAssign 255, 200, 0
    circulo.Outline.SetNoOutline
    sr.Add circulo

    Set txt = lr.CreateArtisticText(0, 0, "JOTAK", , , "Arial", 200, cdrTrue)
    txt.Fill.UniformColor.RGBAssign 255, 255, 255
    txt.CenterX = molde.CenterX
    txt.CenterY = molde.CenterY - 150
    sr.Add txt

    Set g = sr.Group
    g.Name = PREFIXO_ARTE & "FRENTE"
End Sub

Private Sub CriarArteCostas(lr As Layer, molde As Shape)
    Dim sr As ShapeRange, fundo As Shape, nome As Shape, numero As Shape, g As Shape
    Set sr = CreateShapeRange

    Set fundo = lr.CreateRectangle2(molde.CenterX - molde.SizeWidth / 2 - 10, _
                                    molde.CenterY - molde.SizeHeight / 2 - 10, _
                                    molde.SizeWidth + 20, molde.SizeHeight + 20)
    fundo.Fill.UniformColor.RGBAssign 0, 70, 160
    fundo.Outline.SetNoOutline
    sr.Add fundo

    Set nome = lr.CreateArtisticText(0, 0, "NOME", , , "Arial", 160, cdrTrue)
    nome.Fill.UniformColor.RGBAssign 255, 255, 255
    nome.CenterX = molde.CenterX
    nome.CenterY = molde.CenterY + 230
    nome.Name = NOME_TXT_NOME
    sr.Add nome

    Set numero = lr.CreateArtisticText(0, 0, "10", , , "Arial", 700, cdrTrue)
    numero.Fill.UniformColor.RGBAssign 255, 200, 0
    numero.CenterX = molde.CenterX
    numero.CenterY = molde.CenterY - 60
    numero.Name = NOME_TXT_NUMERO
    sr.Add numero

    Set g = sr.Group
    g.Name = PREFIXO_ARTE & "COSTAS"
End Sub

Private Sub CriarPaginaMockup(doc As Document)
    Dim pm As Page, lm As Layer, camisa As Shape, area As Shape, t As Shape
    Set pm = doc.AddPages(1)
    pm.Name = "MOCKUP 1 - Frente"
    pm.SetSize 800, 900
    Set lm = pm.ActiveLayer

    ' Placeholder da foto: troque por uma foto real de camiseta
    Set camisa = lm.CreateRectangle2(100, 100, 600, 700)
    camisa.Fill.UniformColor.RGBAssign 220, 220, 220
    camisa.Outline.SetNoOutline
    camisa.Name = "FOTO_CAMISA"

    Set area = lm.CreateRectangle2(250, 230, 300, 420)
    area.Fill.ApplyNoFill
    area.Outline.Width = 0.5
    area.Name = PREFIXO_AREA & "FRENTE"

    Set t = lm.CreateArtisticText(100, 830, "Troque o retângulo cinza pela foto da camisa", , , "Arial", 36)
    t.Name = "ROTULO"
End Sub
