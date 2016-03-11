using System;
using System.Collections.Generic;
using System.Linq;
using System.Web;

using System.Text;
using MySql.Data.MySqlClient;
using System.Web.Configuration;

namespace Psi4WebServices.Controllers.Data
{
    public class BaseDataAccess
    {
        protected static MySqlConnection conn;

        static BaseDataAccess()
        {
            if (conn == null)
            {
                StringBuilder connectionString = new StringBuilder();
                connectionString.Append("server=");
                connectionString.Append(WebConfigurationManager.AppSettings["SERVER_NAME"]);
                connectionString.Append(";uid=");
                connectionString.Append(WebConfigurationManager.AppSettings["USER_NAME"]);
                connectionString.Append(";pwd=");
                connectionString.Append(WebConfigurationManager.AppSettings["PASSWORD"]);
                connectionString.Append(";database=");
                connectionString.Append(WebConfigurationManager.AppSettings["SCHEMA_NAME"]);
                connectionString.Append(";");

                conn = new MySql.Data.MySqlClient.MySqlConnection();
                conn.ConnectionString = connectionString.ToString();
                try {
                    conn.Open();
                }
                catch (Exception ex)
                {
                    string s = ex.Message;
                }
                
            }
        }

        protected MySqlCommand getCommand(string sql)
        {
            MySqlCommand cmd = new MySqlCommand(sql, conn);
            return cmd;
        }

    }
}
