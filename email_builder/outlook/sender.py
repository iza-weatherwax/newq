"""
outlook/sender.py — Integração com Outlook via win32com.
Cria rascunho (não envia); fallback para arquivo HTML temporário.
"""
from __future__ import annotations


def check_available() -> tuple[bool, str]:
    """
    Verifica se o Outlook está disponível e configurado.
    Retorna (True, "") ou (False, mensagem_de_erro).
    """
    try:
        import pywintypes
        import win32com.client as win32
    except ImportError:
        return False, "pywin32 não está instalado. Execute: pip install pywin32"

    try:
        ol = win32.Dispatch("Outlook.Application")
        _ = ol.Session.CurrentUser  # verifica se há perfil configurado
        return True, ""
    except Exception as exc:
        msg = str(exc)
        if "0x80040154" in msg or "REGDB_E_CLASSNOTREG" in msg:
            return False, "Outlook não está instalado ou registrado no sistema."
        if "profile" in msg.lower() or "0x8004011d" in msg:
            return False, "Outlook não tem perfil configurado. Abra o Outlook e configure uma conta."
        if "access" in msg.lower() or "0x80070005" in msg:
            return False, (
                "Acesso negado ao Outlook. Tente executar o Email Builder "
                "com o mesmo nível de permissão que o Outlook."
            )
        return False, f"Erro ao conectar ao Outlook: {msg}"


def create_draft(
    subject: str,
    body_html: str,
    recipients: list[str] | None = None,
    open_after: bool = True,
) -> tuple[bool, str]:
    """
    Cria um rascunho na pasta Rascunhos do Outlook.

    Args:
        subject: Assunto do email.
        body_html: Corpo HTML do email.
        recipients: Lista de endereços (opcional).
        open_after: Se True, abre o item no Outlook após criar.

    Returns:
        (True, "") em sucesso ou (False, mensagem_de_erro).
    """
    ok, err = check_available()
    if not ok:
        return False, err

    try:
        import win32com.client as win32
        import pywintypes

        ol = win32.Dispatch("Outlook.Application")
        mail = ol.CreateItem(0)  # olMailItem = 0
        mail.Subject = subject
        mail.HTMLBody = body_html

        if recipients:
            for addr in recipients:
                addr = addr.strip()
                if addr:
                    mail.Recipients.Add(addr)

        mail.Save()

        if open_after:
            mail.Display(False)  # False = não modal

        return True, ""

    except Exception as exc:
        import pywintypes
        msg = str(exc)
        if isinstance(exc, pywintypes.com_error):
            hr = exc.args[0] if exc.args else 0
            if hr == -2147221005:
                return False, "Outlook não encontrado ou não registrado."
            if hr == -2147352567:
                return False, "Erro ao criar rascunho. Certifique-se de que o Outlook está aberto."
        return False, f"Erro inesperado ao criar rascunho: {msg}"
