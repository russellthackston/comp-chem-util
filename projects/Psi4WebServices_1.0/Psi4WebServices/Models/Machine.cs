using System;
using System.Collections.Generic;
using System.Linq;
using System.Web;

namespace Psi4WebServices.Models
{
    public class Machine
    {
        public Machine(string name, DateTime created, string mac)
        {
            Name = name;
            Created = created;
            MAC = mac;
        }
        public Machine(int id, string name, DateTime created, string mac)
        {
            ID = id;
            Name = name;
            Created = created;
            MAC = mac;
        }
        public int ID { get; set; }
        public string Name { get; set; }
        public DateTime Created { get; set; }
        public string MAC { get; set; }
    }
}