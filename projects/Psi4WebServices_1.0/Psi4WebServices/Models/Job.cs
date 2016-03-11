using System;
using System.Collections.Generic;
using System.Linq;
using System.Web;

namespace Psi4WebServices.Models
{
    public class Job
    {
        public Job(string name, string inputFile, DateTime created)
        {
            Name = name;
            InputFile = inputFile;
            Created = created;
        }
        public Job(int id, string name, string inputFile, DateTime created)
        {
            ID = id;
            Name = name;
            InputFile = inputFile;
            Created = created;
        }
        public int ID { get; set; }
        public string Name { get; set; }
        public string InputFile { get; set; }
        public DateTime Created { get; set; }
    }
}