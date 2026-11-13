Attribute VB_Name = "SubliProducao"
' =====================================================================
'  Jotak Sublimacao - Moldes por tamanho e Nomes e números
'  Aplica cada ARTE_<PECA> em todos os moldes MOLDE_<PECA>_<TAMANHO>,
'  recorta a arte no formato do molde e já entrega tudo encaixado
'  numa página PRODUCAO pronta para imprimir.
' =====================================================================
Option Explicit

#If VBA7 Then
Private Type OPENFILENAME
    lStructSize As Long
    hwndOwner As LongPtr
    hInstance As LongPtr
    lpstrFilter As String
    lpstrCustomFilter As String
    nMaxCustFilter As Long
    nFilterIndex As Long
    lpstrFile As String
    nMaxFile As Long
    lpstrFileTitle As String
    nMaxFileTitle As Long
    lpstrInitialDir As String
    lpstrTitle As String
    flags As Long
    nFileOffset As Integer
    nFileExtension As Integer
    lpstrDefExt As String
    lCustData As LongPtr
    lpfnHook As LongPtr
    lpTemplateName As String
    pvReserved As LongPtr
    dwReserved As Long
    FlagsEx As Long
End Type
Private Declare PtrSafe Function GetOpenFileName Lib "comdlg32.dll" Alias "GetOpenFileNameA" _
    (pOpenfilename As OPENFILENAME) As Long
#End If

' ---------------------------------------------------------------------
'  MACRO: gera a arte em todos os tamanhos (sem nomes)
' ---------------------------------------------------------------------
Public Sub GerarMoldesPorTamanho()
    Const TITULO As String = "Moldes por tamanho"
    Dim pg As Page, artes As Collection, mapa As Collection
    Dim todos As New Collection, escolhidos As New Collection
    Dim arte As Shape, v As Variant, resp As String, partes() As String, i As Long
    Dim qtd As Double, pedidos As New Collection

    If Not DocumentoOk() Then Exit Sub
    Set pg = ActivePage
    Set artes = ListarArtes(pg)
    If Not ConferirArtes(artes, TITULO) Then Exit Sub
    Set mapa = MapaDeMoldes(pg)

    For Each arte In artes
        For Each v In TamanhosDaPeca(mapa, NomePeca(arte))
            AdicionarSemRepetir todos, CStr(v)
        Next v
    Next arte
    If todos.Count = 0 Then
        MsgBox "Não encontrei nenhum molde. Dê aos moldes nomes como MOLDE_FRENTE_P, " & _
               "MOLDE_FRENTE_M, MOLDE_FRENTE_G...", vbExclamation, TITULO
        Exit Sub
    End If

    resp = InputBox("Tamanhos encontrados: " & Juntar(todos, ", ") & vbCr & vbCr & _
                    "Quais gerar? Separe por vírgula. Deixe vazio para gerar todos.", TITULO, "")
    If StrPtr(resp) = 0 Then Exit Sub
    If Len(Trim$(resp)) = 0 Then
        Set escolhidos = todos
    Else
        partes = Split(Replace(resp, ";", ","), ",")
        For i = LBound(partes) To UBound(partes)
            If Len(Trim$(partes(i))) > 0 Then AdicionarSemRepetir escolhidos, UCase$(Trim$(partes(i)))
        Next i
    End If

    qtd = PerguntarNumero("Quantas peças de cada tamanho?", TITULO, 1)
    If qtd < 1 Then Exit Sub

    For Each v In escolhidos
        pedidos.Add Array(CStr(v), "", "", CLng(qtd))
    Next v
    Produzir pg, artes, mapa, pedidos, False, TITULO
End Sub

' ---------------------------------------------------------------------
'  MACRO: lê a planilha (CSV) e gera uma peça por linha, com nome e número
' ---------------------------------------------------------------------
Public Sub GerarNomesENumeros()
    Const TITULO As String = "Nomes e números"
    Dim pg As Page, artes As Collection, caminho As String, pedidos As Collection, msg As String

    If Not DocumentoOk() Then Exit Sub
    Set pg = ActivePage
    Set artes = ListarArtes(pg)
    If Not ConferirArtes(artes, TITULO) Then Exit Sub

    caminho = EscolherArquivoCsv()
    If Len(caminho) = 0 Then Exit Sub
    If Len(Dir$(caminho)) = 0 Then
        MsgBox "Arquivo não encontrado:" & vbCr & caminho, vbExclamation, TITULO
        Exit Sub
    End If

    On Error GoTo Falha
    Set pedidos = LerPedidosCsv(caminho)
    On Error GoTo 0
    If pedidos.Count = 0 Then
        MsgBox "A planilha não tem nenhuma linha com TAMANHO preenchido.", vbExclamation, TITULO
        Exit Sub
    End If
    Produzir pg, artes, MapaDeMoldes(pg), pedidos, True, TITULO
    Exit Sub
Falha:
    msg = Err.Description
    MsgBox "Erro ao ler a planilha: " & msg, vbCritical, TITULO
End Sub

' ---------------------------------------------------------------------
'  Motor comum
'  pedidos: cada item = Array(tamanho, nome, numero, quantidade)
' ---------------------------------------------------------------------
Private Sub Produzir(pg As Page, artes As Collection, mapa As Collection, pedidos As Collection, _
                     ByVal comTextos As Boolean, ByVal titulo As String)
    Dim pecas As New Collection, avisos As String, msg As String
    Dim p As Variant, arte As Shape, base As Shape, molde As Shape, r As Shape
    Dim peca As String, tam As String, q As Long, nPag As Long

    On Error GoTo Falha
    IniciarOperacao titulo

    For Each p In pedidos
        tam = p(0)
        For q = 1 To p(3)
            For Each arte In artes
                peca = NomePeca(arte)
                Set base = AcharMoldeBase(mapa, peca, arte)
                If base Is Nothing Then
                    Err.Raise vbObjectError + 200, , "Não achei o molde base da peça " & peca & _
                        ". Crie um molde chamado " & PREFIXO_MOLDE & peca & "_" & TAMANHO_BASE & _
                        " e deixe a arte em cima dele."
                End If
                Set molde = ItemDoMapa(mapa, PREFIXO_MOLDE & peca & "_" & tam)
                If molde Is Nothing Then
                    AdicionarAviso avisos, "Não existe o molde " & PREFIXO_MOLDE & peca & "_" & tam
                Else
                    Set r = GerarPeca(arte, base, molde, p(1), p(2), comTextos)
                    r.Name = NomeDaPeca(peca, tam, p(1), p(2))
                    pecas.Add r
                End If
            Next arte
        Next q
    Next p

    If pecas.Count = 0 Then Err.Raise vbObjectError + 201, , "Nenhuma peça foi gerada." & vbCr & avisos

    nPag = Encaixar(pecas, LARGURA_ROLO_MM, ALTURA_MAX_MM, ESPACO_MM, MARGEM_MM, PERMITIR_GIRO, PAGINA_PRODUCAO)
    FinalizarOperacao

    msg = pecas.Count & " peça(s) gerada(s) e encaixada(s) em " & nPag & " página(s) """ & _
          PAGINA_PRODUCAO & """."
    If Len(avisos) > 0 Then msg = msg & vbCr & vbCr & "Atenção:" & vbCr & avisos
    MsgBox msg, IIf(Len(avisos) > 0, vbExclamation, vbInformation), titulo
    Exit Sub
Falha:
    msg = Err.Description
    FinalizarOperacao
    MsgBox "Erro: " & msg & vbCr & vbCr & "Use Ctrl+Z para desfazer o que foi feito.", vbCritical, titulo
End Sub

Private Function ConferirArtes(artes As Collection, ByVal titulo As String) As Boolean
    If artes.Count = 0 Then
        MsgBox "Não encontrei nenhuma arte nesta página." & vbCr & vbCr & _
               "No Gerenciador de Objetos, dê à arte de cada peça um nome como " & _
               "ARTE_FRENTE, ARTE_COSTAS, ARTE_MANGA (agrupe a arte antes).", vbExclamation, titulo
        Exit Function
    End If
    ConferirArtes = True
End Function

Private Function NomeDaPeca(ByVal peca As String, ByVal tam As String, _
                            ByVal nome As String, ByVal numero As String) As String
    Dim r As String
    r = PREFIXO_PECA & peca & "_" & tam
    If Len(nome) > 0 Then r = r & "_" & nome
    If Len(numero) > 0 Then r = r & "_" & numero
    NomeDaPeca = r
End Function

' ---------------------------------------------------------------------
'  Planilha CSV
'  Colunas reconhecidas (em qualquer ordem, com ou sem acento):
'    TAMANHO (obrigatória), NOME, NUMERO, QTD
'  Separador: ponto e vírgula (Excel em português), vírgula ou tab.
' ---------------------------------------------------------------------
Private Function LerPedidosCsv(ByVal caminho As String) As Collection
    Dim res As New Collection, texto As String, linhas() As String, campos As Variant
    Dim i As Long, j As Long, inicio As Long, sep As String
    Dim cNome As Long, cNum As Long, cTam As Long, cQtd As Long
    Dim tam As String, nome As String, numero As String, qtd As Long

    texto = LerArquivoTexto(caminho)
    texto = Replace(texto, vbCrLf, vbLf)
    texto = Replace(texto, vbCr, vbLf)
    linhas = Split(texto, vbLf)

    inicio = -1
    For i = LBound(linhas) To UBound(linhas)
        If Len(Trim$(linhas(i))) > 0 Then
            inicio = i
            Exit For
        End If
    Next i
    If inicio < 0 Then
        Set LerPedidosCsv = res
        Exit Function
    End If

    If InStr(linhas(inicio), vbTab) > 0 Then
        sep = vbTab
    ElseIf InStr(linhas(inicio), ";") > 0 Then
        sep = ";"
    Else
        sep = ","
    End If

    cNome = -1: cNum = -1: cTam = -1: cQtd = -1
    campos = DividirCsv(linhas(inicio), sep)
    For j = LBound(campos) To UBound(campos)
        Select Case NormalizarCabecalho(CStr(campos(j)))
            Case "NOME", "NOMES", "NOMEDACAMISA", "NOMENACAMISA"
                cNome = j
            Case "NUMERO", "NUM", "NRO", "NO", "N", "NUMEROS"
                cNum = j
            Case "TAMANHO", "TAM", "TAMANHOS"
                cTam = j
            Case "QTD", "QTDE", "QUANTIDADE", "QUANT"
                cQtd = j
        End Select
    Next j
    If cTam < 0 Then Err.Raise vbObjectError + 300, , _
        "a planilha precisa de uma coluna TAMANHO (e de preferência NOME e NUMERO) na primeira linha."

    For i = inicio + 1 To UBound(linhas)
        If Len(Trim$(Replace(linhas(i), sep, ""))) > 0 Then
            campos = DividirCsv(linhas(i), sep)
            tam = UCase$(Trim$(Campo(campos, cTam)))
            If Len(tam) > 0 Then
                nome = Trim$(Campo(campos, cNome))
                If NOMES_EM_MAIUSCULAS Then nome = UCase$(nome)
                numero = Trim$(Campo(campos, cNum))
                qtd = 1
                If cQtd >= 0 Then
                    If IsNumeric(Trim$(Campo(campos, cQtd))) Then qtd = CLng(Trim$(Campo(campos, cQtd)))
                    If qtd < 1 Then qtd = 1
                End If
                res.Add Array(tam, nome, numero, qtd)
            End If
        End If
    Next i
    Set LerPedidosCsv = res
End Function

Private Function DividirCsv(ByVal linha As String, ByVal sep As String) As Variant
    Dim partes As New Collection, atual As String, i As Long, c As String, aspas As Boolean
    Dim arr() As String, k As Long
    i = 1
    Do While i <= Len(linha)
        c = Mid$(linha, i, 1)
        If aspas Then
            If c = """" Then
                If Mid$(linha, i + 1, 1) = """" Then
                    atual = atual & """"
                    i = i + 1
                Else
                    aspas = False
                End If
            Else
                atual = atual & c
            End If
        ElseIf c = """" Then
            aspas = True
        ElseIf c = sep Then
            partes.Add atual
            atual = ""
        Else
            atual = atual & c
        End If
        i = i + 1
    Loop
    partes.Add atual
    ReDim arr(0 To partes.Count - 1)
    For k = 1 To partes.Count
        arr(k - 1) = partes(k)
    Next k
    DividirCsv = arr
End Function

Private Function Campo(campos As Variant, ByVal indice As Long) As String
    If indice < LBound(campos) Or indice > UBound(campos) Then Exit Function
    Campo = CStr(campos(indice))
End Function

Private Function NormalizarCabecalho(ByVal t As String) As String
    Dim de As String, para As String, i As Long
    t = UCase$(Trim$(t))
    de = "ÁÀÂÃÄÉÈÊËÍÌÎÏÓÒÔÕÖÚÙÛÜÇ"
    para = "AAAAAEEEEIIIIOOOOOUUUUC"
    For i = 1 To Len(de)
        t = Replace(t, Mid$(de, i, 1), Mid$(para, i, 1))
    Next i
    t = Replace(t, "º", "O")
    t = Replace(t, "°", "O")
    t = Replace(t, ".", "")
    t = Replace(t, " ", "")
    t = Replace(t, "_", "")
    NormalizarCabecalho = t
End Function

Private Function EscolherArquivoCsv() As String
    Dim pasta As String
    pasta = ActiveDocument.FilePath
    If Len(pasta) > 0 And Right$(pasta, 1) <> "\" Then pasta = pasta & "\"

#If VBA7 Then
    Dim ofn As OPENFILENAME, r As Long, f As String
    On Error GoTo Manual
    ofn.lStructSize = LenB(ofn)
    ofn.lpstrFilter = "Planilha CSV (*.csv)" & vbNullChar & "*.csv" & vbNullChar & _
                      "Texto (*.txt)" & vbNullChar & "*.txt" & vbNullChar & _
                      "Todos os arquivos" & vbNullChar & "*.*" & vbNullChar & vbNullChar
    ofn.nFilterIndex = 1
    ofn.lpstrFile = String$(1024, vbNullChar)
    ofn.nMaxFile = 1024
    ofn.lpstrFileTitle = String$(260, vbNullChar)
    ofn.nMaxFileTitle = 260
    ofn.lpstrInitialDir = pasta
    ofn.lpstrTitle = "Escolha a planilha de nomes e números"
    ofn.flags = &H1000& Or &H4&   ' OFN_FILEMUSTEXIST Or OFN_HIDEREADONLY
    r = GetOpenFileName(ofn)
    If r = 0 Then Exit Function    ' cancelou
    f = ofn.lpstrFile
    If InStr(f, vbNullChar) > 0 Then f = Left$(f, InStr(f, vbNullChar) - 1)
    EscolherArquivoCsv = f
    Exit Function
Manual:
#End If
    Dim resp As String
    resp = InputBox("Caminho completo do arquivo CSV:", "Nomes e números", pasta & "nomes.csv")
    If StrPtr(resp) = 0 Then Exit Function
    EscolherArquivoCsv = Trim$(Replace(resp, """", ""))
End Function
