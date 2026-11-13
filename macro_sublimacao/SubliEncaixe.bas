Attribute VB_Name = "SubliEncaixe"
' =====================================================================
'  Jotak Sublimacao - Encaixe inteligente
'  Organiza as peças no papel (rolo ou folhas) girando quando compensa,
'  para gastar o mínimo de papel. Algoritmo: MaxRects com regra
'  "mais acima, depois mais à esquerda" sobre o retângulo de cada peça.
' =====================================================================
Option Explicit

Private Const EPS As Double = 0.001
Private Const ALTURA_INFINITA As Double = 1000000000#

' Retângulos livres do papel (coordenadas a partir do canto superior esquerdo, y para baixo)
Private fx() As Double, fy() As Double, fw() As Double, fh() As Double
Private nLivres As Long

' ---------------------------------------------------------------------
'  MACRO: encaixa os objetos selecionados (ou todos da página) numa
'  nova página ENCAIXE. Os originais não são alterados.
' ---------------------------------------------------------------------
Public Sub EncaixarSelecao()
    Const TITULO As String = "Encaixe inteligente"
    Dim origem As ShapeRange, pecas As New Collection, s As Shape
    Dim largura As Double, altura As Double, nPag As Long, msg As String

    If Not DocumentoOk() Then Exit Sub
    If ActiveSelectionRange.Count > 0 Then
        Set origem = ActiveSelectionRange
    Else
        Set origem = ActivePage.Shapes.All
    End If
    If origem.Count = 0 Then
        MsgBox "Não há objetos para encaixar nesta página.", vbExclamation, TITULO
        Exit Sub
    End If

    largura = PerguntarNumero("Largura útil do papel (mm):", TITULO, LARGURA_ROLO_MM)
    If largura <= 0 Then Exit Sub
    altura = PerguntarNumero("Altura da folha em mm (0 = rolo contínuo):", TITULO, ALTURA_MAX_MM)
    If altura < 0 Then Exit Sub

    On Error GoTo Falha
    IniciarOperacao TITULO
    For Each s In origem
        pecas.Add s.Duplicate
    Next s
    nPag = Encaixar(pecas, largura, altura, ESPACO_MM, MARGEM_MM, PERMITIR_GIRO, PAGINA_ENCAIXE)
    FinalizarOperacao
    MsgBox pecas.Count & " peça(s) encaixada(s) em " & nPag & " página(s) """ & PAGINA_ENCAIXE & """.", _
           vbInformation, TITULO
    Exit Sub
Falha:
    msg = Err.Description
    FinalizarOperacao
    MsgBox "Erro: " & msg & vbCr & vbCr & "Use Ctrl+Z para desfazer o que foi feito.", vbCritical, TITULO
End Sub

' ---------------------------------------------------------------------
'  Encaixa as peças (move-as) em uma ou mais páginas novas.
'  alturaMax = 0 -> rolo contínuo. Devolve o número de páginas criadas.
'  Precisa ser chamada com a unidade do documento em milímetros.
' ---------------------------------------------------------------------
Public Function Encaixar(pecas As Collection, ByVal largura As Double, ByVal alturaMax As Double, _
                         ByVal espaco As Double, ByVal margem As Double, ByVal girar As Boolean, _
                         ByVal nomePagina As String) As Long
    Dim n As Long, i As Long, j As Long, k As Long, t As Long
    Dim w() As Double, h() As Double, ordem() As Long
    Dim px() As Double, py() As Double, rot() As Boolean, folha() As Long, usado() As Double
    Dim binW As Double, binH As Double, x As Double, y As Double, r As Boolean
    Dim pw As Double, ph As Double, restantes As Long, colocadas As Long, nFolhas As Long
    Dim pg As Page, s As Shape, altPag As Double

    n = pecas.Count
    If n = 0 Then Exit Function

    ReDim w(1 To n): ReDim h(1 To n): ReDim ordem(1 To n)
    ReDim px(1 To n): ReDim py(1 To n): ReDim rot(1 To n): ReDim folha(1 To n)
    For i = 1 To n
        w(i) = pecas(i).SizeWidth + espaco
        h(i) = pecas(i).SizeHeight + espaco
        ordem(i) = i
    Next i

    ' Ordena: maior lado primeiro (peças grandes entram antes)
    For i = 2 To n
        t = ordem(i)
        j = i - 1
        Do While j >= 1
            If Chave(w(ordem(j)), h(ordem(j))) >= Chave(w(t), h(t)) Then Exit Do
            ordem(j + 1) = ordem(j)
            j = j - 1
        Loop
        ordem(j + 1) = t
    Next i

    binW = largura - 2 * margem + espaco
    If alturaMax > 0 Then binH = alturaMax - 2 * margem + espaco Else binH = ALTURA_INFINITA
    If binW <= espaco Or binH <= espaco Then Err.Raise vbObjectError + 100, , "Papel menor que as margens."

    restantes = n
    Do While restantes > 0
        nFolhas = nFolhas + 1
        ReDim Preserve usado(1 To nFolhas)
        IniciarLivres binW, binH
        colocadas = 0
        For k = 1 To n
            i = ordem(k)
            If folha(i) = 0 Then
                If MelhorPosicao(w(i), h(i), girar, x, y, r) Then
                    folha(i) = nFolhas
                    px(i) = x: py(i) = y: rot(i) = r
                    If r Then pw = h(i): ph = w(i) Else pw = w(i): ph = h(i)
                    Ocupar x, y, pw, ph
                    If y + ph > usado(nFolhas) Then usado(nFolhas) = y + ph
                    colocadas = colocadas + 1
                    restantes = restantes - 1
                End If
            End If
        Next k
        If colocadas = 0 Then
            For k = 1 To n
                If folha(ordem(k)) = 0 Then
                    Err.Raise vbObjectError + 101, , "A peça """ & pecas(ordem(k)).Name & """ (" & _
                        Format$(w(ordem(k)) - espaco, "0") & " x " & Format$(h(ordem(k)) - espaco, "0") & _
                        " mm) não cabe no papel."
                End If
            Next k
        End If
    Loop

    For k = 1 To nFolhas
        Set pg = NovaPagina(nomePagina)
        If alturaMax > 0 Then
            altPag = alturaMax
        Else
            altPag = usado(k) - espaco + 2 * margem
        End If
        pg.SetSize largura, altPag
        For i = 1 To n
            If folha(i) = k Then
                Set s = pecas(i)
                If rot(i) Then s.Rotate 90
                s.MoveToLayer pg.ActiveLayer
                s.SetPositionEx cdrTopLeft, pg.LeftX + margem + px(i), pg.TopY - margem - py(i)
            End If
        Next i
    Next k

    Encaixar = nFolhas
End Function

Private Function Chave(ByVal w As Double, ByVal h As Double) As Double
    If w > h Then Chave = w Else Chave = h
End Function

' ---------------------------------------------------------------------
'  MaxRects
' ---------------------------------------------------------------------
Private Sub IniciarLivres(ByVal w As Double, ByVal h As Double)
    ReDim fx(1 To 64): ReDim fy(1 To 64): ReDim fw(1 To 64): ReDim fh(1 To 64)
    nLivres = 0
    AdicionarLivre 0, 0, w, h
End Sub

Private Sub AdicionarLivre(ByVal x As Double, ByVal y As Double, ByVal w As Double, ByVal h As Double)
    If w <= EPS Or h <= EPS Then Exit Sub
    nLivres = nLivres + 1
    If nLivres > UBound(fx) Then
        ReDim Preserve fx(1 To nLivres * 2)
        ReDim Preserve fy(1 To nLivres * 2)
        ReDim Preserve fw(1 To nLivres * 2)
        ReDim Preserve fh(1 To nLivres * 2)
    End If
    fx(nLivres) = x: fy(nLivres) = y: fw(nLivres) = w: fh(nLivres) = h
End Sub

' Escolhe a posição que deixa a peça mais para cima (menor y + altura), depois mais à esquerda.
Private Function MelhorPosicao(ByVal w As Double, ByVal h As Double, ByVal girar As Boolean, _
                               ByRef bx As Double, ByRef by As Double, ByRef brot As Boolean) As Boolean
    Dim i As Long, melhorBaixo As Double, melhorX As Double
    melhorBaixo = 1E+300
    melhorX = 1E+300
    For i = 1 To nLivres
        If fw(i) >= w - EPS And fh(i) >= h - EPS Then
            If Melhor(fy(i) + h, fx(i), melhorBaixo, melhorX) Then
                melhorBaixo = fy(i) + h: melhorX = fx(i)
                bx = fx(i): by = fy(i): brot = False
                MelhorPosicao = True
            End If
        End If
        If girar Then
            If fw(i) >= h - EPS And fh(i) >= w - EPS Then
                If Melhor(fy(i) + w, fx(i), melhorBaixo, melhorX) Then
                    melhorBaixo = fy(i) + w: melhorX = fx(i)
                    bx = fx(i): by = fy(i): brot = True
                    MelhorPosicao = True
                End If
            End If
        End If
    Next i
End Function

Private Function Melhor(ByVal baixo As Double, ByVal x As Double, _
                        ByVal melhorBaixo As Double, ByVal melhorX As Double) As Boolean
    If baixo < melhorBaixo - EPS Then
        Melhor = True
    ElseIf Abs(baixo - melhorBaixo) <= EPS And x < melhorX - EPS Then
        Melhor = True
    End If
End Function

' Marca o retângulo (x, y, w, h) como ocupado e recalcula os espaços livres.
Private Sub Ocupar(ByVal x As Double, ByVal y As Double, ByVal w As Double, ByVal h As Double)
    Dim i As Long, n As Long, rx As Double, ry As Double, rw As Double, rh As Double
    n = nLivres
    For i = 1 To n
        If fw(i) > 0 Then
            If x < fx(i) + fw(i) - EPS And x + w > fx(i) + EPS And _
               y < fy(i) + fh(i) - EPS And y + h > fy(i) + EPS Then
                rx = fx(i): ry = fy(i): rw = fw(i): rh = fh(i)
                fw(i) = -1
                If x > rx + EPS Then AdicionarLivre rx, ry, x - rx, rh
                If x + w < rx + rw - EPS Then AdicionarLivre x + w, ry, rx + rw - (x + w), rh
                If y > ry + EPS Then AdicionarLivre rx, ry, rw, y - ry
                If y + h < ry + rh - EPS Then AdicionarLivre rx, y + h, rw, ry + rh - (y + h)
            End If
        End If
    Next i
    RemoverContidos
    Compactar
End Sub

Private Sub RemoverContidos()
    Dim i As Long, j As Long
    For i = 1 To nLivres
        If fw(i) > 0 Then
            For j = 1 To nLivres
                If i <> j And fw(j) > 0 Then
                    If fx(i) >= fx(j) - EPS And fy(i) >= fy(j) - EPS And _
                       fx(i) + fw(i) <= fx(j) + fw(j) + EPS And _
                       fy(i) + fh(i) <= fy(j) + fh(j) + EPS Then
                        fw(i) = -1
                        Exit For
                    End If
                End If
            Next j
        End If
    Next i
End Sub

Private Sub Compactar()
    Dim i As Long, k As Long
    For i = 1 To nLivres
        If fw(i) > 0 Then
            k = k + 1
            fx(k) = fx(i): fy(k) = fy(i): fw(k) = fw(i): fh(k) = fh(i)
        End If
    Next i
    nLivres = k
End Sub
