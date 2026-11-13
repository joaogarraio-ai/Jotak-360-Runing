Attribute VB_Name = "SubliComum"
' =====================================================================
'  Jotak Sublimacao - configuracao e funcoes comuns
'  Macros para CorelDRAW X8 (2016) ou superior, Windows.
' =====================================================================
Option Explicit

'===================== CONFIGURAÇÃO (ajuste aqui) =====================
' Tamanho do molde sobre o qual a arte foi desenhada.
Public Const TAMANHO_BASE As String = "M"
' Largura útil do papel / rolo de sublimação, em mm.
Public Const LARGURA_ROLO_MM As Double = 1600
' Altura da folha em mm. 0 = rolo contínuo (a página cresce o quanto precisar).
' Exemplo para folha A3 em pé: LARGURA_ROLO_MM = 297 e ALTURA_MAX_MM = 420.
Public Const ALTURA_MAX_MM As Double = 0
' Espaço entre as peças no encaixe, em mm.
Public Const ESPACO_MM As Double = 5
' Margem da página de impressão, em mm.
Public Const MARGEM_MM As Double = 10
' O encaixe pode girar as peças 90 graus para aproveitar melhor o papel.
Public Const PERMITIR_GIRO As Boolean = True
' True = a arte é ampliada/reduzida sem distorcer (cobre o molde inteiro).
' False = a arte estica na largura e na altura exatamente como o molde.
Public Const ESCALA_PROPORCIONAL As Boolean = True
' Converte os nomes da planilha para MAIÚSCULAS.
Public Const NOMES_EM_MAIUSCULAS As Boolean = True
' Resolução dos mockups exportados em JPG.
Public Const DPI_MOCKUP As Long = 150
'=====================================================================

' Convenção de nomes dos objetos (Gerenciador de Objetos do CorelDRAW)
Public Const PREFIXO_MOLDE As String = "MOLDE_"
Public Const PREFIXO_ARTE As String = "ARTE_"
Public Const PREFIXO_AREA As String = "AREA_"
Public Const PREFIXO_PECA As String = "PECA_"
Public Const PREFIXO_GERADO As String = "GERADO_"
Public Const NOME_TXT_NOME As String = "TXT_NOME"
Public Const NOME_TXT_NUMERO As String = "TXT_NUMERO"
Public Const PAGINA_PRODUCAO As String = "PRODUCAO"
Public Const PAGINA_ENCAIXE As String = "ENCAIXE"

Private mUnidadeAnterior As Long
Private mEmOperacao As Boolean

' ---------------------------------------------------------------------
'  Controle de operação (desfazer em um passo, velocidade, unidade mm)
' ---------------------------------------------------------------------
Public Function DocumentoOk() As Boolean
    If Documents.Count = 0 Then
        MsgBox "Abra um documento do CorelDRAW primeiro.", vbExclamation, "Jotak Sublimação"
        Exit Function
    End If
    DocumentoOk = True
End Function

Public Sub IniciarOperacao(ByVal titulo As String)
    mUnidadeAnterior = ActiveDocument.Unit
    ActiveDocument.Unit = cdrMillimeter
    ActiveDocument.BeginCommandGroup titulo
    Optimization = True
    EventsEnabled = False
    mEmOperacao = True
End Sub

Public Sub FinalizarOperacao()
    If Not mEmOperacao Then Exit Sub
    mEmOperacao = False
    On Error Resume Next
    EventsEnabled = True
    Optimization = False
    ActiveDocument.EndCommandGroup
    ActiveDocument.Unit = mUnidadeAnterior
    ActiveWindow.Refresh
    Application.Refresh
End Sub

' ---------------------------------------------------------------------
'  Busca de objetos pelo nome
' ---------------------------------------------------------------------
Public Function ComecaCom(ByVal texto As String, ByVal prefixo As String) As Boolean
    ComecaCom = (UCase$(Left$(texto, Len(prefixo))) = UCase$(prefixo))
End Function

' Artes (ARTE_<PECA>) no nível de cima da página.
Public Function ListarArtes(pg As Page) As Collection
    Dim res As New Collection, s As Shape
    For Each s In pg.Shapes
        If ComecaCom(s.Name, PREFIXO_ARTE) Then res.Add s
    Next s
    Set ListarArtes = res
End Function

Public Function NomePeca(arte As Shape) As String
    NomePeca = UCase$(Trim$(Mid$(arte.Name, Len(PREFIXO_ARTE) + 1)))
End Function

' Todos os moldes (MOLDE_*) da página, com o nome em maiúsculas como chave.
Public Function MapaDeMoldes(pg As Page) As Collection
    Dim res As New Collection, s As Shape
    On Error Resume Next
    For Each s In pg.Shapes
        If ComecaCom(s.Name, PREFIXO_MOLDE) Then res.Add s, UCase$(Trim$(s.Name))
    Next s
    On Error GoTo 0
    Set MapaDeMoldes = res
End Function

Public Function ItemDoMapa(mapa As Collection, ByVal chave As String) As Shape
    On Error Resume Next
    Set ItemDoMapa = mapa(UCase$(Trim$(chave)))
    On Error GoTo 0
End Function

' Tamanhos que existem para uma peça: MOLDE_<PECA>_<TAMANHO>
Public Function TamanhosDaPeca(mapa As Collection, ByVal peca As String) As Collection
    Dim res As New Collection, s As Shape, prefixo As String, tam As String
    prefixo = PREFIXO_MOLDE & peca & "_"
    For Each s In mapa
        If ComecaCom(s.Name, prefixo) Then
            tam = UCase$(Trim$(Mid$(s.Name, Len(prefixo) + 1)))
            If Len(tam) > 0 Then AdicionarSemRepetir res, tam
        End If
    Next s
    Set TamanhosDaPeca = res
End Function

' Molde do tamanho base. Se não existir, usa o molde que está embaixo da arte.
Public Function AcharMoldeBase(mapa As Collection, ByVal peca As String, arte As Shape) As Shape
    Dim s As Shape, x As Double, y As Double, w As Double, h As Double
    Set s = ItemDoMapa(mapa, PREFIXO_MOLDE & peca & "_" & TAMANHO_BASE)
    If Not s Is Nothing Then
        Set AcharMoldeBase = s
        Exit Function
    End If
    For Each s In mapa
        If ComecaCom(s.Name, PREFIXO_MOLDE & peca & "_") Then
            s.GetBoundingBox x, y, w, h
            If arte.CenterX >= x And arte.CenterX <= x + w And _
               arte.CenterY >= y And arte.CenterY <= y + h Then
                Set AcharMoldeBase = s
                Exit Function
            End If
        End If
    Next s
End Function

' ---------------------------------------------------------------------
'  Geração de uma peça: arte ajustada ao molde e recortada (PowerClip)
' ---------------------------------------------------------------------
Public Function GerarPeca(arte As Shape, moldeBase As Shape, molde As Shape, _
                          ByVal nome As String, ByVal numero As String, _
                          ByVal trocarTexto As Boolean) As Shape
    Dim sx As Double, sy As Double, dx As Double, dy As Double
    Dim a As Shape, m As Shape

    sx = molde.SizeWidth / moldeBase.SizeWidth
    sy = molde.SizeHeight / moldeBase.SizeHeight
    If ESCALA_PROPORCIONAL Then
        If sx > sy Then sy = sx Else sx = sy
    End If
    dx = arte.CenterX - moldeBase.CenterX
    dy = arte.CenterY - moldeBase.CenterY

    Set m = molde.Duplicate
    m.Name = PREFIXO_PECA & "TMP"     ' para não ser confundido com o molde original
    Set a = arte.Duplicate
    a.Name = PREFIXO_GERADO & "ARTE"

    If trocarTexto Then TrocarTextos a, nome, numero

    a.Stretch sx, sy, True
    a.CenterX = molde.CenterX + dx * sx
    a.CenterY = molde.CenterY + dy * sy
    a.AddToPowerClip m, cdrFalse

    Set GerarPeca = m
End Function

' Troca o conteúdo dos textos TXT_NOME e TXT_NUMERO dentro da arte.
Public Sub TrocarTextos(s As Shape, ByVal nome As String, ByVal numero As String)
    Dim filho As Shape, pc As PowerClip
    Select Case UCase$(Trim$(s.Name))
        Case NOME_TXT_NOME
            If s.Type = cdrTextShape Then s.Text.Story.Text = TextoOuEspaco(nome)
        Case NOME_TXT_NUMERO
            If s.Type = cdrTextShape Then s.Text.Story.Text = TextoOuEspaco(numero)
    End Select
    If s.Type = cdrGroupShape Then
        For Each filho In s.Shapes
            TrocarTextos filho, nome, numero
        Next filho
    End If
    Set pc = Nothing
    On Error Resume Next
    Set pc = s.PowerClip
    On Error GoTo 0
    If Not pc Is Nothing Then
        For Each filho In pc.Shapes
            TrocarTextos filho, nome, numero
        Next filho
    End If
End Sub

Private Function TextoOuEspaco(ByVal t As String) As String
    If Len(t) = 0 Then TextoOuEspaco = " " Else TextoOuEspaco = t
End Function

' ---------------------------------------------------------------------
'  Páginas
' ---------------------------------------------------------------------
Public Function NovaPagina(ByVal nomeBase As String) As Page
    Dim p As Page
    Set p = ActiveDocument.AddPages(1)
    p.Name = NomeDePaginaLivre(nomeBase)
    Set NovaPagina = p
End Function

Private Function NomeDePaginaLivre(ByVal nomeBase As String) As String
    Dim n As Long, candidato As String
    candidato = nomeBase
    n = 1
    Do While ExistePagina(candidato)
        n = n + 1
        candidato = nomeBase & " " & n
    Loop
    NomeDePaginaLivre = candidato
End Function

Private Function ExistePagina(ByVal nome As String) As Boolean
    Dim p As Page
    For Each p In ActiveDocument.Pages
        If UCase$(p.Name) = UCase$(nome) Then
            ExistePagina = True
            Exit Function
        End If
    Next p
End Function

' ---------------------------------------------------------------------
'  Utilidades
' ---------------------------------------------------------------------
Public Sub AdicionarSemRepetir(col As Collection, ByVal valor As String)
    Dim v As Variant
    For Each v In col
        If v = valor Then Exit Sub
    Next v
    col.Add valor
End Sub

Public Function Juntar(col As Collection, ByVal sep As String) As String
    Dim v As Variant, r As String
    For Each v In col
        If Len(r) > 0 Then r = r & sep
        r = r & v
    Next v
    Juntar = r
End Function

Public Sub AdicionarAviso(avisos As String, ByVal msg As String)
    If InStr(1, avisos, msg, vbTextCompare) = 0 Then avisos = avisos & "- " & msg & vbCr
End Sub

' Pede um número. Devolve -1 se o usuário cancelar.
Public Function PerguntarNumero(ByVal pergunta As String, ByVal titulo As String, _
                                ByVal padrao As Double) As Double
    Dim r As String
    Do
        r = InputBox(pergunta, titulo, CStr(padrao))
        If StrPtr(r) = 0 Then
            PerguntarNumero = -1
            Exit Function
        End If
        r = Trim$(r)
        If IsNumeric(r) Then
            PerguntarNumero = CDbl(r)
            Exit Function
        End If
        MsgBox "Digite apenas números.", vbExclamation, titulo
    Loop
End Function

' Lê um arquivo de texto em UTF-8 (com ou sem BOM) ou ANSI (padrão do Excel).
Public Function LerArquivoTexto(ByVal caminho As String) As String
    Dim f As Integer, b() As Byte, tamanho As Long, st As Object, t As String
    f = FreeFile
    Open caminho For Binary Access Read As #f
    tamanho = LOF(f)
    If tamanho = 0 Then
        Close #f
        Exit Function
    End If
    ReDim b(0 To tamanho - 1)
    Get #f, , b
    Close #f

    If PareceUtf8(b) Then
        Set st = CreateObject("ADODB.Stream")
        st.Type = 2
        st.Charset = "utf-8"
        st.Open
        st.LoadFromFile caminho
        t = st.ReadText
        st.Close
        If Len(t) > 0 Then
            If AscW(Left$(t, 1)) = &HFEFF Then t = Mid$(t, 2)
        End If
    Else
        t = StrConv(b, vbUnicode)
    End If
    LerArquivoTexto = t
End Function

Private Function PareceUtf8(b() As Byte) As Boolean
    Dim i As Long, n As Long, k As Long, extras As Long, temMultibyte As Boolean
    n = UBound(b)
    If n >= 2 Then
        If b(0) = &HEF And b(1) = &HBB And b(2) = &HBF Then
            PareceUtf8 = True
            Exit Function
        End If
    End If
    i = 0
    Do While i <= n
        If b(i) < &H80 Then
            extras = 0
        ElseIf (b(i) And &HE0) = &HC0 Then
            extras = 1
        ElseIf (b(i) And &HF0) = &HE0 Then
            extras = 2
        ElseIf (b(i) And &HF8) = &HF0 Then
            extras = 3
        Else
            Exit Function
        End If
        If extras > 0 Then
            If i + extras > n Then Exit Function
            For k = 1 To extras
                If (b(i + k) And &HC0) <> &H80 Then Exit Function
            Next k
            temMultibyte = True
        End If
        i = i + 1 + extras
    Loop
    PareceUtf8 = temMultibyte
End Function
