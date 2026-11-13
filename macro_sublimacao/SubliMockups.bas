Attribute VB_Name = "SubliMockups"
' =====================================================================
'  Jotak Sublimacao - Mockups automáticos
'  Para cada página cujo nome começa com MOCKUP, coloca a arte
'  ARTE_<PECA> dentro do objeto AREA_<PECA> daquela página (recortada
'  no formato da área) e, se pedido, exporta cada mockup em JPG.
'  Rodar de novo substitui os mockups anteriores.
' =====================================================================
Option Explicit

Public Sub GerarMockups()
    Const TITULO As String = "Mockups"
    Dim pgArte As Page, artes As Collection, mapa As Collection, paginas As New Collection
    Dim p As Page, area As Shape, arte As Shape, base As Shape, s As Shape
    Dim peca As String, avisos As String, msg As String, total As Long, exportar As VbMsgBoxResult
    Dim areas As Collection

    If Not DocumentoOk() Then Exit Sub
    Set pgArte = ActivePage
    Set artes = ListarArtes(pgArte)
    If artes.Count = 0 Then
        MsgBox "Vá para a página que tem as artes (ARTE_FRENTE, ARTE_COSTAS...) e rode de novo.", _
               vbExclamation, TITULO
        Exit Sub
    End If
    For Each p In ActiveDocument.Pages
        If ComecaCom(p.Name, "MOCKUP") Then paginas.Add p
    Next p
    If paginas.Count = 0 Then
        MsgBox "Não encontrei páginas de mockup." & vbCr & vbCr & _
               "Crie páginas com nome começando por MOCKUP (ex.: MOCKUP 1 - Frente), " & _
               "coloque a foto da camisa e desenhe sobre ela uma forma chamada AREA_FRENTE " & _
               "(ou AREA_COSTAS...) onde a arte deve aparecer.", vbExclamation, TITULO
        Exit Sub
    End If
    exportar = MsgBox("Encontrei " & paginas.Count & " página(s) de mockup." & vbCr & vbCr & _
                      "Exportar também cada mockup como JPG?", vbYesNoCancel + vbQuestion, TITULO)
    If exportar = vbCancel Then Exit Sub

    Set mapa = MapaDeMoldes(pgArte)

    On Error GoTo Falha
    IniciarOperacao TITULO
    For Each p In paginas
        LimparGerados p
        Set areas = New Collection
        For Each s In p.Shapes
            If ComecaCom(s.Name, PREFIXO_AREA) Then areas.Add s
        Next s
        If areas.Count = 0 Then AdicionarAviso avisos, "A página """ & p.Name & """ não tem nenhuma AREA_..."
        For Each area In areas
            peca = UCase$(Trim$(Mid$(area.Name, Len(PREFIXO_AREA) + 1)))
            Set arte = AcharArte(artes, peca)
            If arte Is Nothing Then
                AdicionarAviso avisos, "Não existe " & PREFIXO_ARTE & peca & " para a " & area.Name & _
                                        " da página """ & p.Name & """"
            Else
                Set base = AcharMoldeBase(mapa, peca, arte)
                AplicarNaArea arte, base, area, peca
                total = total + 1
            End If
        Next area
    Next p
    FinalizarOperacao
    pgArte.Activate

    msg = total & " arte(s) aplicada(s) em " & paginas.Count & " página(s) de mockup."
    If exportar = vbYes Then msg = msg & vbCr & ExportarMockups(paginas)
    If Len(avisos) > 0 Then msg = msg & vbCr & vbCr & "Atenção:" & vbCr & avisos
    MsgBox msg, IIf(Len(avisos) > 0, vbExclamation, vbInformation), TITULO
    Exit Sub
Falha:
    msg = Err.Description
    FinalizarOperacao
    MsgBox "Erro: " & msg & vbCr & vbCr & "Use Ctrl+Z para desfazer o que foi feito.", vbCritical, TITULO
End Sub

Private Function AcharArte(artes As Collection, ByVal peca As String) As Shape
    Dim a As Shape
    For Each a In artes
        If NomePeca(a) = peca Then
            Set AcharArte = a
            Exit Function
        End If
    Next a
End Function

' Apaga os mockups gerados numa rodada anterior.
Private Sub LimparGerados(p As Page)
    Dim apagar As New Collection, s As Shape
    For Each s In p.Shapes
        If ComecaCom(s.Name, PREFIXO_GERADO) Then apagar.Add s
    Next s
    For Each s In apagar
        s.Delete
    Next s
End Sub

' Coloca a arte na área, na mesma posição relativa em que ela está sobre o molde base.
Private Sub AplicarNaArea(arte As Shape, base As Shape, area As Shape, ByVal peca As String)
    Dim a As Shape, c As Shape, sx As Double, sy As Double, dx As Double, dy As Double

    If Not base Is Nothing Then
        sx = area.SizeWidth / base.SizeWidth
        sy = area.SizeHeight / base.SizeHeight
        dx = arte.CenterX - base.CenterX
        dy = arte.CenterY - base.CenterY
    Else
        ' Sem molde: a arte cobre a área toda, centralizada.
        sx = area.SizeWidth / arte.SizeWidth
        sy = area.SizeHeight / arte.SizeHeight
    End If
    If ESCALA_PROPORCIONAL Then
        If sx > sy Then sy = sx Else sx = sy
    End If

    Set a = arte.Duplicate
    a.Name = PREFIXO_GERADO & "ARTE_" & peca
    a.MoveToLayer area.Layer
    a.Stretch sx, sy, True
    a.CenterX = area.CenterX + dx * sx
    a.CenterY = area.CenterY + dy * sy

    Set c = area.Duplicate
    c.Name = PREFIXO_GERADO & peca
    c.Fill.ApplyNoFill
    c.Outline.SetNoOutline
    a.AddToPowerClip c, cdrFalse
    c.OrderFrontOf area
End Sub

' Exporta cada página de mockup como JPG na pasta "mockups" ao lado do arquivo .cdr.
Private Function ExportarMockups(paginas As Collection) As String
    Dim pasta As String, p As Page, arq As String, ef As ExportFilter
    Dim unidade As Long, wpx As Long, hpx As Long, n As Long

    pasta = ActiveDocument.FilePath
    If Len(pasta) = 0 Then
        ExportarMockups = "Os JPG não foram exportados: salve o arquivo .cdr primeiro."
        Exit Function
    End If
    If Right$(pasta, 1) <> "\" Then pasta = pasta & "\"
    pasta = pasta & "mockups\"
    If Len(Dir$(pasta, vbDirectory)) = 0 Then MkDir pasta

    unidade = ActiveDocument.Unit
    ActiveDocument.Unit = cdrInch
    On Error GoTo Falha
    For Each p In paginas
        p.Activate
        wpx = CLng(p.SizeWidth * DPI_MOCKUP)
        hpx = CLng(p.SizeHeight * DPI_MOCKUP)
        arq = pasta & NomeDeArquivo(p.Name) & ".jpg"
        Set ef = ActiveDocument.ExportBitmap(arq, cdrJPEG, cdrCurrentPage, cdrRGBColorImage, _
                                             wpx, hpx, DPI_MOCKUP, DPI_MOCKUP)
        ef.Finish
        n = n + 1
    Next p
    ActiveDocument.Unit = unidade
    ExportarMockups = n & " JPG exportado(s) em " & pasta
    Exit Function
Falha:
    ActiveDocument.Unit = unidade
    ExportarMockups = "Erro ao exportar JPG (" & Err.Description & "). " & n & " exportado(s) em " & pasta
End Function

Private Function NomeDeArquivo(ByVal t As String) As String
    Dim proibidos As String, i As Long
    proibidos = "\/:*?""<>|"
    For i = 1 To Len(proibidos)
        t = Replace(t, Mid$(proibidos, i, 1), "-")
    Next i
    NomeDeArquivo = Trim$(t)
End Function
