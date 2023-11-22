from connection_class import ConnectionClass

handle=ConnectionClass("10.123.66.111", "root", "password",
                       "10.123.66.222", "root", "password")
handle.TestPing()
handle.TestRping(12340)

handle.TestPerfTest(perf_test="ib_write_bw", test_duration=2)
handle.TestPerfTest(perf_test="ib_read_bw", test_duration=2)
handle.TestPerfTest(perf_test="ib_send_bw", test_duration=2)
handle.TestPerfTest(perf_test="ib_atomic_bw", test_duration=2)

handle.TestIPerf(test_duration=10)

handle.ProcessPoller()
