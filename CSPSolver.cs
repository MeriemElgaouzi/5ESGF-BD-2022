using System;
using System.Collections.Generic;
using System.Linq;
using Python.Runtime;
using Sudoku.CSPSparkSolver;
using Sudoku.Shared;




namespace Sudoku.CSPSparkSolver
{

    public enum CSPInference
    {
        None,
        ForwardChecking,
        MAC
    }


    public class CSP_Simple_Solver : CSPSolverBase
    {

    }

    public class CSP_MRV_LCV_Solver : CSPSolverBase
    {

        public CSP_MRV_LCV_Solver()
        {
            UseMRVHeuristics = true;
            UseLCVHeuristics = true;
        }


    }


    public class CSP_ForwardChecking_Solver : CSPSolverBase
    {

        public CSP_ForwardChecking_Solver()
        {
            InferenceType = CSPInference.ForwardChecking;
        }


    }


    public class CSP_ForwardChecking_MRV_Solver : CSP_ForwardChecking_Solver
    {

        public CSP_ForwardChecking_MRV_Solver()
        {
            UseMRVHeuristics = true;
        }


    }

    public class CSP_ForwardChecking_LCV_Solver : CSP_ForwardChecking_Solver
    {

        public CSP_ForwardChecking_LCV_Solver()
        {
            UseLCVHeuristics = true;
        }


    }


    public class CSP_ForwardChecking_MRV_LCV_Solver : CSP_ForwardChecking_MRV_Solver
    {

        public CSP_ForwardChecking_MRV_LCV_Solver()
        {
            UseLCVHeuristics = true;
        }


    }




    public class CSP_Mac_Solver : CSPSolverBase
    {

        public CSP_Mac_Solver()
        {
            InferenceType = CSPInference.MAC;
        }


    }

    public class CSP_Mac_MRV_LCV_Solver : CSP_Mac_Solver
    {

        public CSP_Mac_MRV_LCV_Solver()
        {
            UseMRVHeuristics = true;
            UseLCVHeuristics = true;
        }


    }



    public abstract class CSPSolverBase : PythonSolverBase
    {

        public CSPInference InferenceType { get; set; } = CSPInference.None;

        public bool UseMRVHeuristics { get; set; } = false;

        public bool UseLCVHeuristics { get; set; } = false;
        public object Resources { get; private set; }

        public override GridSudoku Solve(GridSudoku s)
        {
            using (Py.GIL())
            {
                using (PyModule scope = Py.CreateScope())
                {
                    PyObject pySudoku = s.ToPython();


                    //on recupere le choix de l inference de l utilisateur
                    scope.Set("inference", (int)InferenceType);
                    scope.Set("useMRVHeuristics", UseMRVHeuristics);
                    scope.Set("useLCVHeuristics", UseLCVHeuristics);
                    scope.Set("sudoku", pySudoku);

                    object code = CSPSparkSolver.Resources.MainGui;
                    PyModule pyModule = scope.Exec((string)code);

                    var result = scope.Get("sudoku");
                    Console.WriteLine("Sudoku: " + result);
                    var toReturn = result.As<Shared.GridSudoku>();
                    return toReturn;
                }
            }
        }

        protected override void InitializePythonComponents()
        {
            //InstallPipModule("z3-solver"); A adapter au modèle PSO
            base.InitializePythonComponents();
        }
    }
}


