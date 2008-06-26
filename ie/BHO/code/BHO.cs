using System;
using SHDocVw;
using MSHTML;
using Microsoft.Win32;
using System.Runtime.InteropServices;
using System.Runtime.InteropServices.Expando;
using System.Reflection;


namespace BHOSeleniumIce
{
    [
    ComVisible(true),
    ClassInterface(ClassInterfaceType.None)
    ]
    public class ScriptableObject : IScriptableObject
    {
        WebBrowser webBrowser;
        HTMLDocument document;

        public ScriptableObject(WebBrowser browser)
        {
            webBrowser = browser;
            document = webBrowser.Document as HTMLDocument;
        }


        public void helloWorld()
        {
            // Let's make a MessageBox that looks just like a JavaScript alert
            System.Windows.Forms.MessageBox.Show("Hello, World!", 
                                                 "Microsoft Internet Explorer",
                                                 System.Windows.Forms.MessageBoxButtons.OK,
                                                 System.Windows.Forms.MessageBoxIcon.Exclamation);       
        }

        public void showMessage(String textToShow)
        {
            System.Windows.Forms.MessageBox.Show(textToShow, "Microsoft Internet Explorer");
        }

    }

    [
    ComVisible(true),
    // A custom GUID for our BHO
    Guid("8a194578-81ea-4850-9911-13ba2d71efbd"),
    ClassInterface(ClassInterfaceType.None)
    ]
    public class BHO : IObjectWithSite
    {
        WebBrowser webBrowser;
        HTMLDocument document;
        IHTMLWindow2 window;
        IExpando winExpando;

        public void OnDownloadComplete()
        {
            document = webBrowser.Document as HTMLDocument;
            window = document.parentWindow as IHTMLWindow2;

            // In the next few lines, we're going to add a callable
            // object to the "window" namespace exposed to the
            // JavaScript in the browser.
            winExpando = window as IExpando;
            IScriptableObject so = new ScriptableObject(webBrowser);

            // Adding our custom namespace to JavaScript land.
            PropertyInfo myProp = winExpando.AddProperty("ice");
            myProp.SetValue(winExpando, so, null);
        }

        #region BHO Internal Functions

        public static string BHOKEYNAME = "Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Browser Helper Objects";

        [ComRegisterFunction]
        public static void RegisterBHO(Type type)
        {
            RegistryKey registryKey = Registry.LocalMachine.OpenSubKey(BHOKEYNAME, true);

            if (registryKey == null)
                registryKey = Registry.LocalMachine.CreateSubKey(BHOKEYNAME);

            string guid = type.GUID.ToString("B");
            RegistryKey ourKey = registryKey.OpenSubKey(guid);

            if (ourKey == null)
                ourKey = registryKey.CreateSubKey(guid);

            ourKey.SetValue("Alright", 1);
            registryKey.Close();
            ourKey.Close();
        }

        [ComUnregisterFunction]
        public static void UnregisterBHO(Type type)
        {
            RegistryKey registryKey = Registry.LocalMachine.OpenSubKey(BHOKEYNAME, true);
            string guid = type.GUID.ToString("B");

            if (registryKey != null)
                registryKey.DeleteSubKey(guid, false);
        }

        public int SetSite(object site)
        {
            if (site != null)
            {
                webBrowser = (WebBrowser)site;
                webBrowser.DownloadComplete += new DWebBrowserEvents2_DownloadCompleteEventHandler(this.OnDownloadComplete);
            }
            else
            {
                webBrowser.DownloadComplete -= new DWebBrowserEvents2_DownloadCompleteEventHandler(this.OnDownloadComplete);
                webBrowser = null;
            }

            return 0;
        }

        public int GetSite(ref Guid guid, out IntPtr ppvSite)
        {
            IntPtr punk = Marshal.GetIUnknownForObject(webBrowser);
            int hr = Marshal.QueryInterface(punk, ref guid, out ppvSite);
            Marshal.Release(punk);

            return hr;
        }

        #endregion
    }
}
