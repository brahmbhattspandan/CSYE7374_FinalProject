package demo;

import org.junit.Test;
import org.junit.runner.RunWith;
import org.springframework.test.context.web.WebAppConfiguration;

import hello.FinalProjectApplication;

import org.springframework.boot.test.SpringApplicationConfiguration;
import org.springframework.test.context.junit4.SpringJUnit4ClassRunner;

@RunWith(SpringJUnit4ClassRunner.class)
@SpringApplicationConfiguration(classes = FinalProjectApplication.class)
@WebAppConfiguration
public class FinalProjectApplicationTests {

	@Test
	public void contextLoads() {
	}

}
